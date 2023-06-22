CLIENT_ID = "zU4XHVVkc2tDPo4t"
CLIENT_SECRET = "VJKhDFqJPqvsPVNBV6ukXTJmwlvbttP7wlMlrc72se4"

from objects import *
from typing import Tuple
import requests
import time
import random
import json
import base64
import os


class scraper:
    def __init__(
        self,
        quality: str,
        redownload: bool = False,
        authUrlBase: str = "https://auth.tidal.com/v1/oauth2",
        apiUrlBase: str = "https://api.tidalhifi.com/v1",
        clientToken: tuple = (CLIENT_ID, CLIENT_SECRET),
        downloadPath: str = "~/Downloads",
        cachePath: str = "~/.cache",
    ):
        self.quality = quality
        self.redownload = redownload
        self.authUrlBase = authUrlBase
        self.apiUrlBase = apiUrlBase
        self.apiUrlBase = apiUrlBase
        self.clientToken = clientToken
        self.downloadPath = downloadPath
        self.cachePath = cachePath
        authfile = self.cachePath + "/auth.json"
        try:
            with open(authfile, "rb") as f:
                a = json.load(f)
                self.auth = Auth(
                    a["userId"],
                    a["countryCode"],
                    a["accessToken"],
                    a["refreshToken"],
                    a["expiresIn"],
                )
        except (OSError, IndexError):
            self.auth = self.loginByWeb()
            with open(authfile, "w") as f:
                json.dump(self.auth.__dict__, f)

    def post(self, url: str, data: dict) -> dict:
        return requests.post(url, data=data, auth=self.clientToken).json()

    def retrieve(self, url: str, path: str) -> None:
        # TODO: Write function to retrieve stream

    def get(self, url: str, params: dict = {}) -> dict:
        headers = {"authorization": f"Bearer {self.auth.accessToken}"}
        params["countryCode"] = self.auth.countryCode
        err = f"Failed getting {url} "
        for i in range(0, 3):
            try:
                response = requests.get(url, headers=headers, params=params)
                if response.url.find("playbackinfopostpaywall") != -1:
                    sleep_time = random.randint(1, 5)
                    print(f"Pretending to be human, sleeping for {sleep_time}")
                    time.sleep(sleep_time)
                if response.status_code == 429:
                    print("Rate limited, sleeping for 20 seconds")
                    time.sleep(20)
                    continue
                response = response.json()
                if "status" not in response:
                    return response
                if "userMessage" in response and response["userMessage"] is not None:
                    err += f" : {response['userMessage']}"
                break
            except:
                if i >= 3:
                    err += "after 3 tries"
        raise Exception(err)

    def getItems(self, url: str, params: dict = {}) -> list:
        step = 50
        params["limit"] = step
        params["offset"] = 0
        total = 0
        items = []
        while True:
            response = self.get(url, params)
            if "totalNumberOfItems" in response:
                total = response["totalNumberOfItems"]
            if total > 0 and total <= len(items):
                return items
            items += response["items"]
            num = len(response["items"])
            if num < step:
                break
            params["offset"] += step
        return items

    def loginByWeb(self) -> Auth:
        result = self.post(
            f"{self.authUrlBase}/device_authorization",
            {"client_id": self.clientToken[0], "scope": "r_usr+w_usr+w_sub"},
        )
        if "status" in result and result["status"] != 200:
            raise Exception("Client ID not accepted by Tidal")
        login = Login(
            deviceCode=result["deviceCode"],
            userCode=result["userCode"],
            verificationUrl=result["verificationUri"],
            timeout=result["expiresIn"],
            interval=result["interval"],
        )
        elapsed = 0
        timeout = login.timeout if login.timeout else 300
        interval = login.interval if login.interval else 2
        print(f"Log in at https://{login.verificationUrl}/{login.userCode}")
        start = time.time()
        auth = False
        while elapsed < timeout and not auth:
            elapsed = time.time() - start
            result = self.post(
                f"{self.authUrlBase}/token",
                {
                    "client_id": self.clientToken[0],
                    "device_code": login.deviceCode,
                    "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
                    "scope": "r_usr+w_usr+w_sub",
                },
            )
            if "status" in result and result["status"] != 200:
                if result["status"] == 400 and result["sub_status"] == 1002:
                    auth = False  # Not logged in yet
                    continue
                else:
                    raise Exception("Failed to check authorization status")
            auth = Auth(
                result["user"]["userId"],
                result["user"]["countryCode"],
                result["access_token"],
                result["refresh_token"],
                result["expires_in"],
            )
            if not auth:
                time.sleep(interval)
            else:
                return auth
        raise Exception("Failed to log in")

    def getTracks(self, album: Album) -> list:
        return self.getItems(f"{self.apiUrlBase}/albums/{str(album.id)}/items")

    def getAlbumFsPath(self, album: Album) -> str:
        return self.downloadPath + album.title

    def getTrackFsPath(self, track) -> str:
        return f"{self.downloadPath}/{self.getAlbumFsPath(track.album)}/[{track.number}] {track.title}"

    def getStreamInfo(self, track: Track) -> StreamInfo:
        response = self.get(
            f"tracks/{str(track.id)}/playbackinfopostpaywall",
            {
                "audioquality": self.quality,
                "playbackmode": "STREAM",
                "assetpresentation": "FULL",
            },
        )
        if "vnd.tidal.bt" in response["manifestMimeType"]:
            manifest = json.loads(
                base64.b64decode(response["manifest"]).decode("utf-8")
            )
            return StreamInfo(
                response["trackid"],
                response["audioQuality"],
                manifest["codecs"],
                manifest["keyId"] if "keyId" in manifest else "",
                manifest["urls"][0],
            )
        raise Exception("Can't read manifest of type {response['manifestMimeType']}")

    def downloadTrack(self, track, partSize=1048576) -> Tuple[bool, str]:
        try:
            stream = self.getStreamInfo(track.id)
            path = self.getTrackFsPath(track)
            print(f"Starting download of track \"{track.title}\"")
            if not self.redownload and os.path.exists(path):
                print(f"Skipping download, \"{track.title}\" already exists")
                return True, "exists"
            


    def downloadAlbum(self, album: Album):
        tracks = self.getTracks(album)
        for i, track in enumerate(tracks):
            self.downloadTrack(track)
