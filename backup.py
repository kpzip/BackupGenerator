import json
import pysftp
import os
from stat import S_ISDIR, S_ISREG

#TODO, improve this by only reading a certain number of bytes at a time
class FileSystemInterface:   
    
    def writeFile(self, filepath: str, filedata: bytearray) -> None:
        pass
    
    def readFile(self, filepath: str) -> bytearray:
        pass
    
    def getFilesRecursive(self, path: str) -> list:
        pass

class SFTPFileSystem(FileSystemInterface):
    
    def __init__(self, sftpaddr: str, user: str, password: str):
        self.connection = pysftp.Connection(sftpaddr, Username = user, Password = password)
    
    def writeFile(self, filepath: str, filedata: bytearray) -> None:
        pass
    
    def readFile(self, filepath: str) -> bytearray:
        pass
        
    def getFilesRecursive(self, path: str) -> list:
        pass

class LocalFileSystem(FileSystemInterface):
    
    def __init__(self):
        pass
    
    def writeFile(self, filepath: str, filedata: bytearray) -> None:
        with open(filepath, "wb") as file:
            file.write(filedata)
    
    def readFile(self, filepath: str) -> bytearray:
        with open(filepath, "rb") as file:
            return file.read()
    
    def getFilesRecursive(self, path: str) -> list:
        filelist = []
        for (root, dirs, files) in os.walk(path):
            for file in files:
                filelist.append((root + file).removeprefix(path))
        return filelist
        

def file_system_factory(fstype: str, config: dict) -> FileSystemInterface:
    if (fstype == "sftp"):
        return SFTPFileSystem(config["sftp_addr"], config["sftp_user"], config["sftp_pass"])
    if (fstype == "local"):
        return LocalFileSystem()
    return None
    
def copy_file(fs_in: FileSystemInterface, fs_out: FileSystemInterface, dir_in: str, dir_out: str) -> None:
    fs_out.writeFile(dir_out, fs_in.readFile(dir_in))

def main():
    print("Initiating Backup...")
    cfgfile = open("config.json")
    cfg = json.load(cfgfile)
    cfgfile.close()
    fs_from = file_system_factory(cfg["from"], cfg)
    fs_to = file_system_factory(cfg["to"], cfg)
    print(str(fs_from.getFilesRecursive("C:\\Users\\kpzip\\Desktop\\rust\\")))
    for file in cfg["files"]:
        copy_file(fs_from, fs_to, file["from"], file["to"])
    for directory in cfg["folders"]:
        for file in fs_from.get(directory)
            copy_file(fs_from, fs_to, directory["from"] + file, directory["to"] + file)
    print("Backup Complete!")

if __name__ == "__main__":
    main()
