#!/bin/python3

CLIENT_ID = "zU4XHVVkc2tDPo4t"
CLIENT_SECRET = "VJKhDFqJPqvsPVNBV6ukXTJmwlvbttP7wlMlrc72se4"
URL_BASE = "https://auth.tidal.com/v1/oauth2"

import requests
import time
import json
from dataclasses import dataclass


@dataclass
class Login:
    deviceCode: str | None
    userCode: str | None
    verificationUrl: str | None
    timeout: int | None
    interval: int | None


@dataclass
class Auth:
    userId: str | None
    countryCode: str | None
    accessToken: str | None
    refreshToken: str | None
    expiresIn: str | None


def post(path, data, auth=None) -> dict:
    return requests.post(URL_BASE + path, data=data, auth=auth).json()


def getLogin() -> Login:
    data = {"client_id": CLIENT_ID, "scope": "r_usr+w_usr+w_sub"}

    result = post("/device_authorization", data)

    if "status" in result and result["status"] != 200:
        raise Exception("Client ID not accepted by Tidal")

    return Login(
        deviceCode=result["deviceCode"],
        userCode=result["userCode"],
        verificationUrl=result["verificationUri"],
        timeout=result["expiresIn"],
        interval=result["interval"],
    )


def getAuth(login: Login) -> Auth | None:
    data = {
        "client_id": CLIENT_ID,
        "device_code": login.deviceCode,
        "grant_type": "urn:ietf:params:oauth:grant-type:device_code",
        "scope": "r_usr+w_usr+w_sub",
    }

    result = post("/token", data, (CLIENT_ID, CLIENT_SECRET))

    if "status" in result and result["status"] != 200:
        if result["status"] == 400 and result["sub_status"] == 1002:
            return None  # Not logged in yet
        else:
            raise Exception("Failed to check authorization status")

    return Auth(
        result["user"]["userId"],
        result["user"]["countryCode"],
        result["access_token"],
        result["refresh_token"],
        result["expires_in"],
    )


def loginByWeb() -> Auth:
    login = getLogin()
    url = f"http://{login.verificationUrl}/{login.userCode}"
    print(f"Log in at {url}")

    start = time.time()
    elapsed = 0
    timeout = login.timeout if login.timeout else 300
    interval = login.interval if login.interval else 2

    while elapsed < timeout:
        elapsed = time.time() - start
        auth = getAuth(login)
        if not auth:
            time.sleep(interval)
        else:
            return auth

    raise Exception("Failed to log in")


if __name__ == "__main__":
    try:
        with open("auth.json", "rb") as f:
            a = json.load(f)
            auth = Auth(a['userId'], a['countryCode'], a['accessToken'], a['refreshToken'], a['expiresIn'])
    except (OSError, IndexError):
        auth = loginByWeb()
        with open("auth.json", "w") as f:
            json.dump(auth.__dict__, f)
