CLIENT_ID = "zU4XHVVkc2tDPo4t"
CLIENT_SECRET = "VJKhDFqJPqvsPVNBV6ukXTJmwlvbttP7wlMlrc72se4"
API_URL_BASE = "https://api.tidalhifi.com/v1"
AUTH_URL_BASE = "https://auth.tidal.com/v1/oauth2"


from objects import *
import requests
import time
import random
import json


class scraper:
    def __init__(self, authfile: str):
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
        return requests.post(url, data=data, auth=(CLIENT_ID, CLIENT_SECRET)).json()

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
            f"{AUTH_URL_BASE}/device_authorization",
            {"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"},
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
                f"{AUTH_URL_BASE}/token",
                {
                    "client_id": CLIENT_ID,
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

    def getTracks(self, obj) -> list:
        url = API_URL_BASE
        if type(obj) is Album:
            url += f"/albums/{str(obj.id)}/items"
        elif type(obj) is Playlist:
            url += f"/playlists/{obj.uuid}/items"
        else:
            raise Exception("Tried to get tracks from incorrect object")
        return self.getItems(url)

    def downloadAlbum(self, album: Album):
        tracks = self.getTracks(album)
        # TODO: Continue working here
