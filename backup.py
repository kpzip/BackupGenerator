import json
import pysftp as sftp
import os
import getpass
from typing import Self, Generator
from typing_extensions import override
from io import BufferedIOBase, TextIOWrapper

from paramiko import SFTPFile

# Modify if you want the config file named something else, or in another directory
config_names: list[str] = ["config.json"]


# Represents an abstract file system that can be written to and read from
class FileSystemInterface:

    def __init__(self) -> None:
        self.isclosed: bool = False

    def writeFile(self, filepath: str, filedata: bytes, append: bool = True) -> None:
        raise NotImplementedError

    def readFile(self, filepath: str, chunk_size: int) -> Generator[bytes, None, None]:
        raise NotImplementedError

    def getFilesRecursive(self, path: str) -> list:
        raise NotImplementedError

    def close(self) -> None:
        pass

    def closeIfNotClosed(self) -> None:
        if not self.isclosed:
            self.close()
            self.isclosed = True

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        self.closeIfNotClosed()

    def __del__(self):
        self.closeIfNotClosed()


# TODO update in the future to allow for both key and user/password authentication
class SFTPFileSystem(FileSystemInterface):

    def __init__(self, sftpaddr: str, user: str, password: str, port: int) -> None:
        super().__init__()
        self.address: str = sftpaddr
        self.username: str = user
        self.password: str = password
        self.port: int = port
        self.write_file: SFTPFile | None = None
        self.write_path: str = ""
        self.write_mode: bool = False

    @override
    def writeFile(self, filepath: str, filedata: bytes, append: bool = True) -> None:
        if self.write_file is None or self.write_path != filepath or self.write_mode != append:
            if self.write_file is not None:
                self.write_file.close()
            self.write_file = self.connection.open(filepath, "ab" if append else "wb")
            self.write_path = filepath
            self.write_mode = append
        self.write_file.write(filedata)

        # file: SFTPFile
        # with self.connection.open(filepath, "wb") as file:
        #     file.write(filedata)

    @override
    def readFile(self, filepath: str, chunk_size: int) -> Generator[bytes, None, None]:
        file: SFTPFile
        with self.connection.open(filepath, "rb") as file:
            read_bytes: bytes
            while read_bytes := file.read(chunk_size):
                yield read_bytes

    @override
    def getFilesRecursive(self, path: str) -> list:
        filelist: list[str] = []

        def addFile(file: str) -> None:
            nonlocal filelist
            filelist.append(file)

        self.connection.walktree(path, addFile, lambda d: None, addFile, recurse=True)
        return filelist

    @override
    def close(self) -> None:
        if self.write_file is not None:
            self.write_file.close()
        self.connection.close()

    @override
    def __enter__(self) -> Self:
        self.connection: sftp.Connection = sftp.Connection(self.address,
                                                           username=self.username,
                                                           password=self.password,
                                                           port=self.port)
        return self


class LocalFileSystem(FileSystemInterface):

    def __init__(self) -> None:
        super().__init__()
        self.write_file: BufferedIOBase | None = None
        self.write_path: str = ""
        self.write_mode: bool = False

    @override
    def writeFile(self, filepath: str, filedata: bytes, append: bool = True) -> None:
        if self.write_file is None or self.write_path != filepath or self.write_mode != append:
            if self.write_file is not None:
                self.write_file.close()
            if self.write_path != filepath:
                os.makedirs(os.path.dirname(filepath), exist_ok=True)
            self.write_file = open(filepath, "ab" if append else "wb")
            self.write_path = filepath
            self.write_mode = append
        self.write_file.write(filedata)

        # file: BufferedIOBase
        # with open(filepath, "wb") as file:
        #     file.write(filedata)

    @override
    def readFile(self, filepath: str, chunk_size: int) -> Generator[bytes, None, None]:
        file: BufferedIOBase
        with open(filepath, "rb") as file:
            read_bytes: bytes
            while read_bytes := file.read(chunk_size):
                yield read_bytes

    @override
    def getFilesRecursive(self, path: str) -> list:
        filelist: list[str] = []
        root: str
        dirs: list[str]
        files: list[str]
        for (root, dirs, files) in os.walk(path):
            file: str
            for file in files:
                filelist.append((os.path.relpath(root, path) + "\\" + file))
        return filelist

    @override
    def close(self) -> None:
        if self.write_file is not None:
            self.write_file.close()


class GoogleDriveFileSystem(FileSystemInterface):

    def __init__(self) -> None:
        super().__init__()

    @override
    def writeFile(self, filepath: str, filedata: bytes, append: bool = True) -> None:
        raise NotImplementedError

    @override
    def readFile(self, filepath: str, chunk_size: int) -> Generator[bytes, None, None]:
        raise NotImplementedError

    @override
    def getFilesRecursive(self, path: str) -> list:
        raise NotImplementedError


# Use this if transferring from sftp to sftp since it prevents multiple different connections from being established
# In the future, It may be possible to go from one sftp server to another, in that case this will need to be rewritten
existingSftpConnection: SFTPFileSystem | None = None


def file_system_factory(fstype: str, config: dict) -> FileSystemInterface:
    global existingSftpConnection

    # Read the true type from the config
    fstype = config[fstype]

    if fstype == "sftp":
        if existingSftpConnection is None:
            addr: str = config["sftp_addr"]
            user: str = config["sftp_user"]
            passwd: str = config["sftp_pass"]
            port: int
            if "sftp_port" in config:
                port = config["sftp_port"]
            elif "port" in config:
                port = config["port"]
            else:
                port = 22
            if user == "prompt":
                user = input("SFTP username for address " + addr + " :")
            if passwd == "prompt":
                passwd = getpass.getpass(prompt=("SFTP password for address " + addr + " :"))
            existingSftpConnection = SFTPFileSystem(addr, user, passwd, port)
        return existingSftpConnection
    if fstype == "local":
        return LocalFileSystem()
    return LocalFileSystem()


def copy_file(fs_in: FileSystemInterface, fs_out: FileSystemInterface, path_in: str, path_out: str,
              chunk_size: int) -> None:
    file_reader: Generator[bytes, None, None] = fs_in.readFile(path_in, chunk_size)
    chunk: bytes
    try:
        chunk = file_reader.__next__()
        fs_out.writeFile(path_out, chunk, append=False)
    except StopIteration:
        # This is the case when the file is empty, so we need to write an empty file.
        fs_out.writeFile(path_out, b"", append=False)
    for chunk in file_reader:
        fs_out.writeFile(path_out, chunk, append=True)

    # fs_out.writeFile(path_out, fs_in.readFile(path_in))


def main(config_locations: list[str]) -> None:
    # loop through each config name and execute backup
    for i in range(0, len(config_locations)):

        config_location: str = config_locations[i]
        print("Initiating Backup (" + str(i + 1) + "/" + str(len(config_locations)) + ") ...")

        cfgfile: TextIOWrapper
        with open(config_location) as cfgfile:
            cfg: dict = json.load(cfgfile)

        # Create objects for interfacing with filesystem(s)
        fs_from: FileSystemInterface
        fs_to: FileSystemInterface
        with file_system_factory("from", cfg) as fs_from, file_system_factory("to", cfg) as fs_to:

            # Copy individual files
            file: dict[str, str]
            for file in cfg["files"]:
                copy_file(fs_from, fs_to, file["from"], file["to"], cfg["maxbytes"])

            # Copy folders
            directory: dict[str, str]
            for directory in cfg["folders"]:
                filename: str
                for filename in fs_from.getFilesRecursive(directory["from"]):
                    copy_file(fs_from, fs_to, directory["from"] + filename, directory["to"] + filename, cfg["maxbytes"])

        print("Backup Complete!")


if __name__ == "__main__":
    main(config_names)
