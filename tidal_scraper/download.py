import tidal_scraper.metadata as metadata
from tidal_scraper.helper import extensions, clean_template, log_error

import tidalapi
import os
import json
import requests
import io
import time
import random
from tqdm import tqdm
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util import Counter
from typing import Tuple
from typing import BinaryIO

MASTER_KEY = (
    b"P\x89SLC&\x98\xb7\xc6\xa3\n?P.\xb4\xc7a\xf8\xe5n\x8cth\x13E\xfa?\xbah8\xef\x9e"
)


def __decode_key_id(key_id: str) -> Tuple[bytes, bytes]:
    decoded_key_id = b64decode(key_id)
    init_vector = decoded_key_id[:16]
    encrypted_token = decoded_key_id[16:]

    decryptor = AES.new(MASTER_KEY, AES.MODE_CBC, init_vector)
    decrypted_token = decryptor.decrypt(encrypted_token)

    key = decrypted_token[:16]
    nonce = decrypted_token[16:24]

    return key, nonce


def __decrypt_file(fp: BinaryIO, key: bytes, nonce: bytes) -> None:
    counter = Counter.new(64, prefix=nonce, initial_value=0)
    decryptor = AES.new(key, AES.MODE_CTR, counter=counter)
    fp.seek(0)
    data = fp.read()
    data = decryptor.decrypt(data)
    fp.write(data)


def __download_file(url: str, fp: BinaryIO) -> str:
    with requests.get(url, stream=True) as r:
        r.raise_for_status()
        mime = r.headers.get("Content-Type", "")
        total_bytes = int(r.headers.get("Content-Length", 0))
        with tqdm(total=total_bytes, unit="iB", unit_scale=True) as p:
            for data in r.iter_content(1024):
                fp.write(data)
                p.update(len(data))
    return mime


def download_track(
    track: tidalapi.Track,
    sleep: bool,
    conf: dict | None = None,
    name_template: str | None = None,
    dest_dir: str | None = None,
    skip_downloaded: bool | None = None,
    errorfile: str | None = None,
) -> None:
    album = track.album
    assert album
    assert album.artist
    if conf is None:
        assert skip_downloaded is not None
        assert errorfile is not None
        assert name_template is not None
        assert dest_dir is not None
    else:
        skip_downloaded = skip_downloaded or conf["skip_downloaded"]
        errorfile = errorfile or conf["error_log"]
        dest_dir = dest_dir or conf["dest_dir"]
        name_template = name_template or conf["track_name"]

    dest = dest_dir + clean_template(name_template, track=track)
    print(f"Starting {album.artist.name} - {track.name}")
    http_failures = 0
    while http_failures <= 3:
        try:
            stream = track.stream()
            manifest = json.loads(b64decode(stream.manifest))
            url = manifest["urls"][0]
            codec = manifest["codecs"]
            if ".mp4" in url:
                if "ac4" in codec or "mha1" in codec:
                    dest += ".mp4"
                else:
                    dest += ".m4a"
            else:
                for ext in extensions:
                    if ext in url:
                        dest += ext
                        break
            if os.path.exists(dest) and skip_downloaded:
                print("Skipping track\n")
                if sleep:
                    t = random.randrange(750, 1500) / 1000
                    time.sleep(t)
                return

            assert track.name and album.name
            with io.BytesIO() as b:
                print("Downloading track")
                key_id = manifest.get("keyId", None)
                mime = __download_file(url, b)
                if key_id:
                    print("Decrypting track")
                    __decrypt_file(b, *__decode_key_id(key_id))
                    metadata.write(
                        b,
                        mime,
                        track.name,
                        album.name,
                        str(track.track_num),
                        str(album.num_tracks),
                    )
                with open(dest, "wb") as f:
                    data = b.getvalue()
                    f.write(data)
            print()
            if sleep:
                t = random.randrange(1000, 5000) / 1000
                time.sleep(t)
            break
        except requests.HTTPError:
            http_failures += 1
            t = random.randrange(10000, 20000) / 1000
            time.sleep(t)
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            log_error(
                errorfile or "error.log",
                "Failure while downloading {artist} - {track}",
                artist=album.artist.name,
                track=track.name,
            )
            break


def download_cover(
    obj: tidalapi.Album | tidalapi.Playlist,
    conf: dict | None = None,
    dest: str | None = None,
    size: int | None = None,
    skip_dl: bool | None = None,
) -> None:
    if conf is None:
        assert dest is not None
        assert size is not None
        assert skip_dl is not None
    else:
        if type(obj) is tidalapi.Album:
            dest = clean_template(
                conf["dest_dir"] + "/" + conf["album_dir"],
                album=obj,
            )
            size = conf["album_image_size"]
        elif type(obj) is tidalapi.Playlist:
            dest = clean_template(
                conf["dest_dir"] + "/" + conf["playlist_dir"],
                playlist=obj,
            )
            size = conf["playlist_image_size"]

        skip_dl = conf["skip_downloaded"]
        assert dest
        assert size

    if os.path.exists(dest) and skip_dl:
        return

    url = obj.image(size)
    with open(dest, "wb") as f:
        __download_file(url, f)


def download_album(album: tidalapi.Album, conf: dict) -> None:
    dest = clean_template(
        conf["dest_dir"] + "/" + conf["album_dir"],
        album=album,
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    download_cover(album, conf)
    tracks = album.tracks()
    for track in tracks:
        download_track(track, True, conf, dest_dir=dest)


def download_playlist(playlist: tidalapi.Playlist, conf: dict) -> None:
    dest = clean_template(
        conf["dest_dir"] + "/" + conf["playlist_dir"],
        playlist=playlist,
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    download_cover(playlist, conf)
    tracks = playlist.tracks()
    for track in tracks:
        download_track(track, True, conf, dest_dir=dest)


def download_artist(artist: tidalapi.Artist, conf: dict) -> None:
    albums = artist.get_albums()
    for album in albums:
        download_album(album, conf)
