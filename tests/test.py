import json
import sys
import os
# kind of a hack, but so be it
directory = os.getcwd().removesuffix("\\tests")
sys.path.insert(1, directory)
import backup

#enable and define colors
os.system("color")

GREEN = '\033[92m'
RED = '\033[91m'
RESET = '\033[00m'


# Get config values
testconfig = "test_config.json"

with open(testconfig, "r") as configfile:
    config = json.load(configfile)
    maxbytes = config["maxbytes"]
    files = config["files"]
    folders = config["folders"]

#file system object for reading file data 
fs = backup.LocalFileSystem()

#whether or not a test has failed yet
passing = True

#verify if a file exists and if it has the contents as the supplied master file
def verifyFile(backup: str, master: str) -> None:
    try:
        with open(backup, "rb") as b, open(master, "rb") as m:
            while (readdata := m.read(maxbytes)) != b"":
                assert readdata == b.read(maxbytes)
    except FileNotFoundError:
        print("Missing file! : " + file["to"])
        passing = False
    except AssertionError:
        print("Wrong file data! : " + file["to"])
        passing = False
    
    
#run tests
def test() -> None:
    backup.main(testconfig)
    for file in files:
        verifyFile(file["to"], file["from"])
    for directory in folders:
        for file in fs.getFilesRecursive(directory["from"]):
            verifyFile(directory["to"] + file, directory["from"] + file)
    print("Done!")
    print("------------------------")
    print((GREEN + "BUILD SUCCESSFUL" + RESET) if passing else (RED + "BUILD FAILED" + RESET))
    print("------------------------")
    if not passing:
        exit(-1)

if __name__ == "__main__":
    test()