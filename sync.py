import sys
import time
from pathlib import Path


def sync(from_dir: Path, to_dir: Path) -> None:
    for obj in from_dir.iterdir():
        print(f"Move {str(obj)} to {str(to_dir)}")
        obj.rename(to_dir / obj.name)


def parse_args() -> tuple[Path, Path]:
    args = sys.argv[1:]
    args_length = len(args)

    if args_length != 2 and args_length != 4:
        raise Exception("Invalid arguments. example: python sync.py from=<from_dir> to=<to_dir>")
    elif args_length == 2:
        raw_from, raw_to = args
        from_key, from_value = raw_from.split("=")
        to_key, to_value = raw_to.split("=")
    else:
        from_key, from_value, to_key, to_value = args

    if from_key != "from" and to_key != "to":
        raise Exception("Invalid arguments. example: python sync.py from=<from_dir> to=<to_dir>")

    from_dir = Path(from_value)
    to_dir = Path(to_value)

    if not from_dir.is_dir() or not from_dir.exists():
        raise Exception("\"from_dir\" should be a directory and exists")
    if not to_dir.is_dir() or not to_dir.exists():
        raise Exception("\"to_dir\" should be a directory and exists")

    return from_dir, to_dir


def main() -> None:
    from_dir, to_dir = parse_args()

    print("Syncing...")
    try:
        while True:
            sync(from_dir=from_dir, to_dir=to_dir)
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped syncing")


if __name__ == "__main__":
    main()
