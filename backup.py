import json
import pysftp
import os
from stat import S_ISDIR, S_ISREG

#Thanks, stackoverflow
def get_r_portable(sftp, remotedir, localdir, preserve_mtime=False):
    for entry in sftp.listdir_attr(remotedir):
        remotepath = remotedir + "/" + entry.filename
        localpath = os.path.join(localdir, entry.filename)
        mode = entry.st_mode
        if S_ISDIR(mode):
            try:
                os.mkdir(localpath)
            except OSError:     
                pass
            get_r_portable(sftp, remotepath, localpath, preserve_mtime)
        elif S_ISREG(mode):
            sftp.get(remotepath, localpath, preserve_mtime=preserve_mtime)

def main():
    print("Initiating Backup...")
    cfgfile = open("config.json")
    cfg = json.load(cfg)
    cfgfile.close()
    if cfg["from"] == "sftp" and cfg["to"] == "local":
        sftp = pysftp.Connection(cfg["sftp_addr"], Username = cfg["sftp_user"], Password = cfg["sftp_pass"])
        for filedata in cfg["files"]:
            get_r_portable(sftp, filedata[0], filedata[1], preserve_mtime = True)
        sftp.close()

if __name__ == "__main__":
    main()
