import metadata
from helper import CONF, EXTENSIONS, clean_template, log_error

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
    data = decryptor.decrypt(fp)
    fp.write(data)


def __download_file(url: str, fp: BinaryIO) -> None:
    r = requests.get(url, stream=True)
    r.raise_for_status()
    total_bytes = int(r.headers.get("content-length", 0))
    progress = tqdm(total=total_bytes, unit="iB", unit_scale=True)
    for data in r.iter_content(1024):
        fp.write(data)
        progress.update(len(data))
    progress.close()


def download_track(track: tidalapi.Track, dest_path: str) -> None:
    album = track.album
    assert album
    dest_path += clean_template(CONF["track_name"], track=track)

    try:
        stream = track.stream()
        manifest = json.loads(b64decode(stream.manifest))
        print(manifest)
        url = manifest["urls"][0]
        for ext in EXTENSIONS:
            if ext in url and ext is not ".mp4":
                dest_path += ext
            elif ".mp4" in url:
                if "ac4" in stream.codec or "mha1" in stream.codec:
                    dest_path += ".mp4"
                else:
                    dest_path += ".m4a"
            if os.path.exists(dest_path + ext) and CONF["skip_downloaded"]:
                print(f"Skipping {album.artist.name} - {track.name}")
                return

        assert track.name and album.name
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with io.BytesIO() as b:
            print(f"Downloading {album.artist.name} - {track.name}")
            key_id = manifest.get("keyId", None)
            __download_file(url, b)

        if key_id:
            __decrypt_file(b, *__decode_key_id(key_id))
            metadata.write(
                b,
                manifest["codecs"],
                track.name,
                album.name,
                str(track.track_num),
                str(album.num_tracks),
            )
            with open(dest_path, "wb") as f:
                data = b.read()
                f.write(data)
    except:
        log_error(
            "Failure while downloading {artist} - {track}",
            artist=album.artist.name,
            track=track.name,
        )


def download_cover(
    obj: tidalapi.Album | tidalapi.Playlist, dest_path: str, size: int
) -> None:
    if os.path.exists(dest_path) and CONF["skip_downloaded"]:
        return

    url = obj.image(size)
    with open(dest_path, "wb") as f:
        __download_file(url, f)


def download_album(album: tidalapi.Album) -> None:
    dest_path = clean_template(
        CONF["dest_dir"] + CONF["album_dir"],
        album=album,
        artist=album.artist,
    )
    download_cover(album, dest_path, CONF["album_image_size"])
    tracks = album.tracks()
    for track in tracks:
        download_track(track, dest_path)


def download_playlist(playlist: tidalapi.Playlist) -> None:
    dest_path = clean_template(
        CONF["dest_dir"] + CONF["playlist_dir"],
        playlist=playlist,
    )
    download_cover(playlist, dest_path, CONF["playlist_image_size"])
    tracks = playlist.tracks()
    for track in tracks:
        download_track(track, dest_path)


def download_artist(artist: tidalapi.Artist) -> None:
    albums = artist.get_albums()
    for album in albums:
        download_album(album)
