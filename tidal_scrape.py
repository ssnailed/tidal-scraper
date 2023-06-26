#!/bin/env python3
import tidalapi
import aigpy
import aigpy.downloadHelper
import json
import sys
import base64
import os
import time
from Crypto.Cipher import AES
from Crypto.Util import Counter
from typing import Tuple
from datetime import datetime

USER_ID = os.getenv("USER_ID")
# Must be on same disk unless you replace the
# os.replace on line 105 with something better
DL_PATH = os.getenv("DL_PATH")
DEST_PATH = os.getenv("DEST_PATH")
AUTH_PATH = os.getenv("AUTH_PATH")
SKIP_DOWNLOADED = bool(os.getenv("SKIP_DOWNLOADED"))

config = tidalapi.Config(quality=tidalapi.Quality.lossless)
session = tidalapi.Session(config)


def decrypt_token(token) -> Tuple[bytes, bytes]:
    master_key = "UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754="
    master_key = base64.b64decode(master_key)
    security_token = base64.b64decode(token)
    iv = security_token[:16]
    encrypted_st = security_token[16:]

    decryptor = AES.new(master_key, AES.MODE_CBC, iv)
    decrypted_st = decryptor.decrypt(encrypted_st)

    key = decrypted_st[:16]
    nonce = decrypted_st[16:24]

    return key, nonce


def decrypt_file(input_file, output_file, key, nonce) -> None:
    counter = Counter.new(64, prefix=nonce, initial_value=0)
    decryptor = AES.new(key, AES.MODE_CTR, counter=counter)

    with open(input_file, "rb") as i:
        data = decryptor.decrypt(i.read())

        with open(output_file, "wb") as o:
            o.write(data)


def set_metadata(track: tidalapi.Track, file: str) -> None:
    # This function could be more fleshed out (lyrics, covers)
    # but I will leave that to external programs
    tagger = aigpy.tag.TagTool(file)

    tagger.title = track.name
    tagger.artist = list(map(lambda artist: artist.name, track.artists))  # type: ignore[reportOptionalMemberAccess]
    tagger.copyright = track.copyright
    tagger.tracknumber = track.track_num
    tagger.discnumber = track.volume_num

    tagger.album = track.album.name  # type: ignore[reportOptionalMemberAccess]
    tagger.albumartist = list(map(lambda artist: artist.name, track.album.artists))  # type: ignore[reportOptionalMemberAccess]
    tagger.date = track.album.available_release_date  # type: ignore[reportOptionalMemberAccess]
    tagger.totaldisc = track.album.num_volumes or 0  # type: ignore[reportOptionalMemberAccess]
    if tagger.totaldisc <= 1:
        tagger.totaltrack = track.album.num_tracks  # type: ignore[reportOptionalMemberAccess]

    tagger.save()


def download_track(
    track: tidalapi.Track,
    partSize: int = 1048576,
) -> Tuple[bool, str]:
    try:
        dl_path = f"{DL_PATH}/{track.album.name}/{track.name}.part"  # type: ignore[reportOptionalMemberAccess]
        dest_path = f"{DEST_PATH}/{track.album.name}/{track.name}"  # type: ignore[reportOptionalMemberAccess]

        print(f"Downloading {track.name} - {track.artist.name}")  # type: ignore[reportOptionalMemberAccess]

        if os.path.exists(dest_path) and SKIP_DOWNLOADED:
            print(dest_path + " exists!")
            return True, "Skipping downloaded song"

        stream = track.stream()

        stream.manifest = json.loads(base64.b64decode(stream.manifest))
        url = stream.manifest["urls"][0]
        try:
            key = stream.manifest["keyId"]
        except KeyError:
            key = None
        tool = aigpy.downloadHelper.DownloadTool(dl_path, [url])

        tool.setPartSize(partSize)
        check, err = tool.start(True, 1)
        if not check:
            return False, str(err)

        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        if key:
            key, nonce = decrypt_token(key)
            decrypt_file(dl_path, dest_path, key, nonce)
        else:
            os.replace(dl_path, dest_path)

        set_metadata(track, dest_path)

        return True, "Successfully downloaded!"
    except Exception as msg:
        return False, str(msg)


auth_path = f"{AUTH_PATH}/auth.json"
try:
    with open(auth_path, "rb") as f:
        a = json.load(f)
        expiry_time = a["expiry_time"].split(".", 1)[0]
        expiry_time = datetime.strptime(expiry_time, "%Y-%m-%d %H:%M:%S")
        session.load_oauth_session(
            a["token_type"], a["access_token"], a["refresh_token"], expiry_time
        )
    os.chmod(auth_path, 0o600)
except (OSError, IndexError):
    session.login_oauth_simple()

if session.check_login():
    with open(auth_path, "w") as f:
        json.dump(
            {
                "token_type": session.token_type,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expiry_time": str(session.expiry_time),
            },
            f,
        )
else:
    sys.exit("Failed to log in")

user = session.get_user(USER_ID)
favorites = tidalapi.user.Favorites(session, user.id)
tracks = favorites.tracks()

for track in tracks:
    print(f"Downloading {track.album.name} by {track.artist}")
    check, msg = download_track(track)
    print(msg)
    time.sleep(3)
