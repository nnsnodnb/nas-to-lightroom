import shutil
import time
from pathlib import Path


def sync():
    _from = Path("/Volumes/photo/sftp")
    _to = Path("/Users/nnsnodnb/Pictures/nas")
    _to.mkdir(exist_ok=True)

    for obj in _from.iterdir():
        print(f"Move {str(obj)} to {str(_to)}")
        shutil.copy(obj, _to)
        obj.unlink()


if __name__ == "__main__":
    print("Syncing...")
    while True:
        sync()
        time.sleep(10)
