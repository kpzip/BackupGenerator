import json
import sys
import os

# kind of a hack, but so be it
script_directory = os.getcwd().removesuffix("\\tests")
sys.path.insert(1, script_directory)
import backup

# enable and define colors
os.system("color")

GREEN: str = '\033[92m'
RED: str = '\033[91m'
RESET: str = '\033[00m'

# Get config values
testconfig = "test_config.json"

with open(testconfig, "r") as configfile:
    config: dict = json.load(configfile)
    max_bytes: int = config["maxbytes"]
    files: list[dict[str, str]] = config["files"]
    folders: list[dict[str, str]] = config["folders"]

# file system object for reading file data
fs = backup.LocalFileSystem()

# whether a test has failed yet
passing: bool = True


# verify if a file exists and if it has the contents as the supplied master file
def verifyFile(backup_dir: str, master_dir: str) -> None:
    global passing
    try:
        with open(backup_dir, "rb") as b, open(master_dir, "rb") as m:
            while (read_data := m.read(max_bytes)) != b"":
                assert read_data == b.read(max_bytes)
    except FileNotFoundError:
        print("Missing file! : " + backup_dir)
        passing = False
    except AssertionError:
        print("Wrong file data! : " + backup_dir)
        passing = False


# run tests
def test() -> None:
    backup.main([testconfig])
    for file in files:
        verifyFile(file["to"], file["from"])
    for directory in folders:
        for file in fs.getFilesRecursive(directory["from"]):
            verifyFile(directory["to"] + file, directory["from"] + file)
    print("Done!")
    print("------------------------")
    print((GREEN + "TEST SUCCESSFUL" + RESET) if passing else (RED + "TEST FAILED" + RESET))
    print("------------------------")
    if not passing:
        exit(-1)


if __name__ == "__main__":
    test()
