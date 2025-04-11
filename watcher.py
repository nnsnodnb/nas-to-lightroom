import os
import time
from pathlib import Path

from watchdog.events import DirCreatedEvent, FileCreatedEvent, FileSystemEventHandler
from watchdog.observers import Observer

from lightroom import LightroomAPI


class EventHandler(FileSystemEventHandler):
    lightroom: LightroomAPI
    catalog_id: str | None = None
    album_id: str | None = None

    def __init__(self) -> None:
        self.lightroom = LightroomAPI(
            client_id=os.environ["CLIENT_ID"],
            client_secret=os.environ["CLIENT_SECRET"],
            refresh_token=os.environ["REFRESH_TOKEN"],
        )
        self.catalog_id = self.lightroom.get_catalog()
        albums = self.lightroom.list_albums(self.catalog_id)
        for obj in albums:
            if obj["type"] == "album" and obj["payload"]["name"] == "2025_04_phpcon_odawara":
                self.album_id = obj["id"]
                break
        else:
            raise Exception(f"No album found in {self.catalog_id}")

    def on_created(self, event: DirCreatedEvent | FileCreatedEvent) -> None:
        if (
            event.event_type != 'created'
            or event.is_directory
            or not event.src_path.lower().endswith(".jpg")
        ):
            return

        asset_id = self.lightroom.upload_photo(self.catalog_id, Path(event.src_path))
        self.lightroom.add_asset_to_album(self.catalog_id, self.album_id, asset_id)


def watch() -> None:
    watch_path = Path("/") / "Users" / "nnsnodnb" / "Pictures" / "nas"
    if not watch_path.exists():
        raise FileNotFoundError(f"File not found: {watch_path}")

    event_handler = EventHandler()
    # return
    observer = Observer()
    observer.schedule(event_handler, str(watch_path) + "/", recursive=False)

    print(f"Starting to watch for file changes in {str(watch_path)}/.")
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down")
        observer.stop()
    finally:
        observer.join()


if __name__ == "__main__":
    watch()
