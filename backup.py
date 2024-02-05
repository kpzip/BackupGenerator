import json
import pysftp
import os
from stat import S_ISDIR, S_ISREG

#TODO, improve this by only reading a certain number of bytes at a time
class FileSystemInterface:   
    
    def write(self, filepath: str, filedata: bytearray) -> None:
        pass
    
    def read(self, filepath: str) -> bytearray:
        pass
        

class SFTPFileSystem(FileSystemInterface):
    
    def __init__(self, sftpaddr: str, user: str, password: str):
        self.connection = pysftp.Connection(sftpaddr, Username = user, Password = password)
    
    def write(self, filepath: str, filedata: bytearray) -> None:
        pass
    
    def read(self, filepath: str) -> bytearray:
        pass

class LocalFileSystem(FileSystemInterface):
    
    def __init__(self):
        pass
    
    def write(self, filepath: str, filedata: bytearray) -> None:
        pass
    
    def read(self, filepath: str) -> bytearray:
        pass

def file_system_factory(fstype: str, config: dict) -> FileSystemInterface:
    if (fstype == "sftp"):
        return SFTPFileSystem(config["sftp_addr"], config["sftp_user"], config["sftp_pass"])
    if (fstype == "local"):
        return LocalFileSystem()
    return None

def main():
    print("Initiating Backup...")
    cfgfile = open("config.json")
    cfg = json.load(cfg)
    cfgfile.close()
    fs_from = file_system_factory(cfg["from"], cfg)
    fs_to = file_system_factory(cfg["to"], cfg)
    for file in cfg["files"]:
        to.write(file, from.read(file))
    print("Backup Complete!")

if __name__ == "__main__":
    main()
