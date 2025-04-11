import json
import uuid
from datetime import datetime
from pathlib import Path

import requests


class LightroomAPI:
    client_id: str
    client_secret: str
    access_token: str | None
    refresh_token: str
    account_id: str | None

    def __init__(
        self, client_id: str, client_secret: str, refresh_token: str,
    ) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.initialize()

    def initialize(self) -> None:
        self.refresh_access_token()
        self.set_account_id()

    @staticmethod
    def parse_json(response: requests.Response) -> dict:
        try:
            return response.json()
        except json.decoder.JSONDecodeError:
            # including 'while (1) {}' on top of the response
            return json.loads(response.text.splitlines()[1])

    def get_common_headers(self) -> dict:
        return {
            "X-API-Key": self.client_id,
            "Authorization": f"Bearer {self.access_token}",
        }

    def refresh_access_token(self) -> None:
        url = "https://ims-na1.adobelogin.com/ims/token"
        params = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token",
        }
        res = requests.post(url, params=params)
        res.raise_for_status()
        data = self.parse_json(res)
        self.access_token = data["access_token"]
        self.refresh_token = data["refresh_token"]

    def set_account_id(self) -> None:
        url = "https://lr.adobe.io/v2/account"
        headers = self.get_common_headers()
        res = requests.get(url, headers=headers)

        if res.status_code == 401:
            self.refresh_access_token()
            self.set_account_id()
            return

        res.raise_for_status()
        data = self.parse_json(res)
        self.account_id = data["id"]

    def get_catalog(self) -> str:
        url = "https://lr.adobe.io/v2/catalog"
        headers = self.get_common_headers()
        res = requests.get(url, headers=headers)

        if res.status_code == 401:
            self.refresh_access_token()
            return self.get_catalog()

        res.raise_for_status()
        data = self.parse_json(res)
        catalog_id = data["id"]

        return catalog_id

    def list_albums(self, catalog_id: str) -> list[dict]:
        url = f"https://lr.adobe.io/v2/catalogs/{catalog_id}/albums"
        headers = self.get_common_headers()
        res = requests.get(url, headers=headers)

        if res.status_code == 401:
            self.refresh_access_token()
            return self.list_albums(catalog_id)

        res.raise_for_status()
        data = self.parse_json(res)

        return data["resources"]

    def upload_photo(self, catalog_id: str, image_path: Path) -> str:
        def create_asset(asset_id: str | None = None) -> str:
            asset_id = asset_id or str(uuid.uuid4()).replace("-", "")
            url = f"https://lr.adobe.io/v2/catalogs/{catalog_id}/assets/{asset_id}"
            headers = self.get_common_headers()
            data = {
                "subtype": "image",
                "payload": {
                    "captureDate": "0000-00-00T00:00:00",
                    "importSource": {
                        "fileName": image_path.name,
                        "importedOnDevice": "Google Pixel 4a (5G)",
                        "importedBy": self.account_id,
                        "importTimestamp": datetime.now().isoformat(),
                    },
                }
            }
            res = requests.put(url, headers=headers, json=data)

            if res.status_code == 401:
                self.refresh_access_token()
                return create_asset(asset_id)

            res.raise_for_status()

            return asset_id

        def upload_photo(asset_id: str) -> None:
            url = f"https://lr.adobe.io/v2/catalogs/{catalog_id}/assets/{asset_id}/master"
            headers = self.get_common_headers()
            headers.update({"Content-Type": "image/jpeg"})
            res = requests.put(url, headers=headers, data=image_path.read_bytes())

            if res.status_code == 401:
                self.refresh_access_token()
                upload_photo(asset_id)
                return

            res.raise_for_status()

        asset = create_asset()
        upload_photo(asset)

        return asset

    def add_asset_to_album(self, catalog_id: str, album_id: str, asset_id: str) -> None:
        url = f"https://lr.adobe.io/v2/catalogs/{catalog_id}/albums/{album_id}/assets"
        headers = self.get_common_headers()
        data = {
            "resources": [
                {
                    "id": asset_id,
                    "payload": {
                        "cover": False,
                    },
                },
            ],
        }
        res = requests.put(url, headers=headers, json=data)

        if res.status_code == 401:
            self.refresh_access_token()
            self.add_asset_to_album(catalog_id, album_id, asset_id)
            return

        res.raise_for_status()
        data = self.parse_json(res)
        print(data)
