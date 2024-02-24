import json
import pysftp as sftp
import os
import getpass
from typing import Self
from io import BufferedIOBase, TextIOWrapper

# Modify if you want the config file named something else, or in another directory
config_names: list[str] = ["config.json"]


# TODO, improve this by only reading a certain number of bytes at a time
class FileSystemInterface:

    def writeFile(self, filepath: str, filedata: bytes) -> None:
        raise NotImplementedError

    def readFile(self, filepath: str) -> bytes:
        raise NotImplementedError

    def getFilesRecursive(self, path: str) -> list:
        raise NotImplementedError

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args) -> None:
        pass


class SFTPFileSystem(FileSystemInterface):

    def __init__(self, sftpaddr: str, user: str, password: str):
        self.address: str = sftpaddr
        self.username: str = user
        self.password: str = password

    def writeFile(self, filepath: str, filedata: bytes) -> None:
        file: BufferedIOBase
        with self.connection.open(filepath, "wb") as file:
            file.write(filedata)

    def readFile(self, filepath: str) -> bytes:
        file: BufferedIOBase
        with self.connection.open(filepath, "rb") as file:
            return file.read()

    def getFilesRecursive(self, path: str) -> list:
        pass

    def __enter__(self) -> Self:
        self.connection: sftp.Connection = sftp.Connection(self.address, username=self.username, password=self.password)
        return self

    def __exit__(self, *args) -> None:
        self.connection.close()


class LocalFileSystem(FileSystemInterface):

    def __init__(self):
        pass

    def writeFile(self, filepath: str, filedata: bytes) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        file: BufferedIOBase
        with open(filepath, "wb") as file:
            file.write(filedata)

    def readFile(self, filepath: str) -> bytes:
        file: BufferedIOBase
        with open(filepath, "rb") as file:
            return file.read()

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


def file_system_factory(fstype: str, config: dict) -> FileSystemInterface:
    if fstype == "sftp":
        addr: str = config["sftp_addr"]
        user: str = config["sftp_user"]
        passwd: str = config["sftp_pass"]
        if user == "prompt":
            user = input("SFTP username for address " + addr + " :")
        if passwd == "prompt":
            passwd = getpass.getpass(prompt=("SFTP password for address " + addr + " :"))
        return SFTPFileSystem(addr, user, passwd)
    if fstype == "local":
        return LocalFileSystem()
    return LocalFileSystem()


def copy_file(fs_in: FileSystemInterface, fs_out: FileSystemInterface, dir_in: str, dir_out: str) -> None:
    fs_out.writeFile(dir_out, fs_in.readFile(dir_in))


def main(config_locations: list[str]) -> None:
    for i in range(0, len(config_locations)):
        config_location: str = config_locations[i]
        print("Initiating Backup (" + str(i) + "/" + str(len(config_locations)) + ") ...")
        cfgfile: TextIOWrapper
        with open(config_location) as cfgfile:
            cfg: dict = json.load(cfgfile)
        fs_from: FileSystemInterface
        fs_to: FileSystemInterface
        with file_system_factory(cfg["from"], cfg) as fs_from, file_system_factory(cfg["to"], cfg) as fs_to:
            file: dict[str, str]
            for file in cfg["files"]:
                copy_file(fs_from, fs_to, file["from"], file["to"])
            directory: dict[str, str]
            for directory in cfg["folders"]:
                file: str
                for file in fs_from.getFilesRecursive(directory["from"]):
                    copy_file(fs_from, fs_to, directory["from"] + file, directory["to"] + file)
        print("Backup Complete!")


if __name__ == "__main__":
    main(config_names)
