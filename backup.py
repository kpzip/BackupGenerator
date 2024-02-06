import json
import pysftp as sftp
import os

#TODO, improve this by only reading a certain number of bytes at a time
class FileSystemInterface:   
    
    def writeFile(self, filepath: str, filedata: str) -> None:
        pass
    
    def readFile(self, filepath: str) -> str:
        pass
    
    def getFilesRecursive(self, path: str) -> list:
        pass

class SFTPFileSystem(FileSystemInterface):
    
    def __init__(self, sftpaddr: str, user: str, password: str):
        self.connection = sftp.Connection(sftpaddr, Username = user, Password = password)
    
    def writeFile(self, filepath: str, filedata: str) -> None:
        pass
    
    def readFile(self, filepath: str) -> str:
        pass
        
    def getFilesRecursive(self, path: str) -> list:
        pass

class LocalFileSystem(FileSystemInterface):
    
    def __init__(self):
        pass
    
    def writeFile(self, filepath: str, filedata: str) -> None:
        os.makedirs(os.path.dirname(filepath), exist_ok = True)
        with open(filepath, "wb") as file:
            file.write(filedata)
    
    def readFile(self, filepath: str) -> str:
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
        return SFTPFileSystem(config["sftp_addr"], config["sftp_user"], config["sftp_pass"])
    if (fstype == "local"):
        return LocalFileSystem()
    return None
    
def copy_file(fs_in: FileSystemInterface, fs_out: FileSystemInterface, dir_in: str, dir_out: str) -> None:
    fs_out.writeFile(dir_out, fs_in.readFile(dir_in))

def main(configLocation: str) -> None:
    print("Initiating Backup...")
    cfgfile = open(configLocation)
    cfg = json.load(cfgfile)
    cfgfile.close()
    fs_from = file_system_factory(cfg["from"], cfg)
    fs_to = file_system_factory(cfg["to"], cfg)
    for file in cfg["files"]:
        copy_file(fs_from, fs_to, file["from"], file["to"])
    for directory in cfg["folders"]:
        for file in fs_from.getFilesRecursive(directory["from"]):
            copy_file(fs_from, fs_to, directory["from"] + file, directory["to"] + file)
    print("Backup Complete!")

if __name__ == "__main__":
    main("config.json")
