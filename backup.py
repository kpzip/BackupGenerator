import json
import pysftp as sftp
import os
import getpass

#Modify if you want the config file named something else, or in another directory
config_name = "config.json"

#TODO, improve this by only reading a certain number of bytes at a time
class FileSystemInterface:   
    
    def writeFile(self, filepath: str, filedata: bytes) -> None:
        pass
    
    def readFile(self, filepath: str) -> bytes:
        pass
    
    def getFilesRecursive(self, path: str) -> list:
        pass

class SFTPFileSystem(FileSystemInterface):
    
    def __init__(self, sftpaddr: str, user: str, password: str):
        self.connection = sftp.Connection(sftpaddr, Username = user, Password = password)
    
    def writeFile(self, filepath: str, filedata: bytes) -> None:
        pass
    
    def readFile(self, filepath: str) -> bytes:
        pass
        
    def getFilesRecursive(self, path: str) -> list:
        pass

class LocalFileSystem(FileSystemInterface):
    
    def __init__(self):
        pass
    
    def writeFile(self, filepath: str, filedata: bytes) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok = True)
        with open(filepath, "wb") as file:
            file.write(filedata)
    
    def readFile(self, filepath: str) -> bytes:
        with open(filepath, "rb") as file:
            return file.read()
    
    def getFilesRecursive(self, path: str) -> list:
        filelist = []
        for (root, dirs, files) in os.walk(path):
            for file in files:
                filelist.append((os.path.relpath(root, path) + "\\" + file))
        return filelist
        

def file_system_factory(fstype: str, config: dict) -> FileSystemInterface:
    if (fstype == "sftp"):
        addr = config["sftp_addr"]
        user = config["sftp_user"]
        passwd = config["sftp_pass"]
        if user == "prompt":
            user = input("SFTP username for address " + addr + " :")
        if passwd == "prompt":
            passwd = getpass.getpass(prompt=("SFTP password for address " + addr + " :"))
        return SFTPFileSystem(config["sftp_addr"], config["sftp_user"], config["sftp_pass"])
    if (fstype == "local"):
        return LocalFileSystem()
    return None
    
def copy_file(fs_in: FileSystemInterface, fs_out: FileSystemInterface, dir_in: str, dir_out: str) -> None:
    fs_out.writeFile(dir_out, fs_in.readFile(dir_in))

def main(configLocation: str) -> None:
    print("Initiating Backup...")
    with open(configLocation) as cfgfile:
        cfg = json.load(cfgfile)
    fs_from = file_system_factory(cfg["from"], cfg)
    fs_to = file_system_factory(cfg["to"], cfg)
    for file in cfg["files"]:
        copy_file(fs_from, fs_to, file["from"], file["to"])
    for directory in cfg["folders"]:
        for file in fs_from.getFilesRecursive(directory["from"]):
            copy_file(fs_from, fs_to, directory["from"] + file, directory["to"] + file)
    print("Backup Complete!")

if __name__ == "__main__":
    main(config_name)
