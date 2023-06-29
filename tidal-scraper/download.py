import metadata
from helper import conf, extensions, clean_template, log_error

import tidalapi
import os
import json
import requests
import io
from tqdm import tqdm
from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util import Counter
from typing import Tuple
from typing import BinaryIO

# MASTER_KEY = b64decode("UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754=")
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
        if conf["debug"]:
            print(r.headers)
        r.raise_for_status()
        mime = r.headers.get("Content-Type", "")
        total_bytes = int(r.headers.get("Content-Length", 0))
        with tqdm(total=total_bytes, unit="iB", unit_scale=True) as p:
            for data in r.iter_content(1024):
                fp.write(data)
                p.update(len(data))
    return mime


def download_track(track: tidalapi.Track, dest: str) -> None:
    album = track.album
    assert album
    print(f"Starting {album.artist.name} - {track.name}")
    dest += clean_template(conf["track_name"], track=track)
    http_failures = 0
    while http_failures <= 3:
        try:
            stream = track.stream()
            manifest = json.loads(b64decode(stream.manifest))
            if conf["debug"]:
                print(manifest)
            url = manifest["urls"][0]
            codec = manifest["codecs"]
            if ".mp4" in url:
                if "ac4" in codec or "mha1" in codec:
                    dest += ".mp4"
                else:
                    dest += ".m4a"
            else:
                for ext in (x for x in extensions if x != ".mp4"):
                    dest += ext
            if os.path.exists(dest) and conf["skip_downloaded"]:
                print(f"Skipping track")
                return

            assert track.name and album.name
            with io.BytesIO() as b:
                print(f"Downloading track")
                key_id = manifest.get("keyId", None)
                mime = __download_file(url, b)
                if key_id:
                    print(f"Decrypting track")
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
            break
        except requests.HTTPError:
            http_failures += 1
        except:
            log_error(
                "Failure while downloading {artist} - {track}",
                artist=album.artist.name,
                track=track.name,
            )
            break


def download_cover(
    obj: tidalapi.Album | tidalapi.Playlist, dest: str, size: int
) -> None:
    if os.path.exists(dest) and conf["skip_downloaded"]:
        return

    url = obj.image(size)
    with open(dest, "wb") as f:
        __download_file(url, f)


def download_album(album: tidalapi.Album) -> None:
    dest = clean_template(
        conf["dest_dir"] + "/" + conf["album_dir"],
        album=album,
        artist=album.artist,
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    download_cover(album, dest, conf["album_image_size"])
    tracks = album.tracks()
    for track in tracks:
        download_track(track, dest)


def download_playlist(playlist: tidalapi.Playlist) -> None:
    dest = clean_template(
        conf["dest_dir"] + "/" + conf["playlist_dir"],
        playlist=playlist,
    )
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    download_cover(playlist, dest, conf["playlist_image_size"])
    tracks = playlist.tracks()
    for track in tracks:
        download_track(track, dest)


def download_artist(artist: tidalapi.Artist) -> None:
    albums = artist.get_albums()
    for album in albums:
        download_album(album)
