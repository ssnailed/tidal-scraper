import helper
from helper import CONF, EXTENSIONS
import metadata

import tidalapi
import os
import json

from base64 import b64decode
from Crypto.Cipher import AES
from Crypto.Util import Counter
from typing import Tuple, BinaryIO
from shutil import move


def __decode_key_id(key_id) -> Tuple[bytes, bytes]:
    master_key = b64decode("UIlTTEMmmLfGowo/UC60x2H45W6MdGgTRfo/umg4754=")
    decoded_key_id = b64decode(key_id)
    init_vector = decoded_key_id[:16]
    encrypted_token = decoded_key_id[16:]

    decryptor = AES.new(master_key, AES.MODE_CBC, init_vector)
    decrypted_token = decryptor.decrypt(encrypted_token)

    key = decrypted_token[:16]
    nonce = decrypted_token[16:24]

    return key, nonce


def __decrypt_file(
    input_file: BinaryIO, output_file: BinaryIO, key: bytes, nonce: bytes
) -> None:
    counter = Counter.new(64, prefix=nonce, initial_value=0)
    decryptor = AES.new(key, AES.MODE_CTR, counter=counter)
    data = decryptor.decrypt(input_file.read())
    output_file.write(data)


def set_metadata():
    pass


def download_track(
    track: tidalapi.Track,
    album: tidalapi.Album,
) -> None:
    dl_path = helper.clean_template(CONF["dl_dir"])
    dest_path = helper.clean_template(
        CONF["dest_dir"] + CONF["album_dir"] + CONF["track_name"],
        track=track,
        album=album,
        artist=album.artist,
    )
    try:
        stream = track.stream()
        manifest = json.loads(b64decode(stream.manifest))
        url = manifest["urls"][0]
        codec = manifest['codecs']
        for ext in EXTENSIONS:
            if ext in url and ext is not ".mp4":
                dest_path += ext
            elif ".mp4" in url:
                if "ac4" in stream.codec or "mha1" in stream.codec:
                    dest_path += ".mp4"
                else:
                    dest_path += ".m4a"
            if os.path.exists(dest_path + ext) and CONF["skip_downloaded"]:
                print("Skipping downloaded song")
                return

        key_id = manifest.get("keyId", None)
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            # TODO: DOWNLOAD
            pass

        if key_id:
            key, nonce = __decode_key_id(key_id)
            with open(dl_path, "rb") as i, open(dest_path, "wb") as o:
                __decrypt_file(i, o, key, nonce)
        else:
            move(dl_path, dest_path)

        assert track.name is not None
        assert album.name is not None
        metadata.write(f, codec, track.name, album.name, str(track.track_num), str(album.num_tracks))
    except:
        assert album.artist is not None
        helper.log_error(
            "Failure while downloading {artist} - {album} - {track}:",
            artist=album.artist.name,
            album=album.name,
            track=track.name,
        )
        # stack trace is printed by log_error()


def download_cover(album: tidalapi.Album) -> None:
    dest_path = helper.clean_template(
        CONF["dest_dir"] + CONF["album_dir"],
        album=album,
        artist=album.artist,
    )
    url = album.image(1280)

    if os.path.exists(dest_path) and CONF["skip_downloaded"]:
        return

    # TODO: DOWNLOAD
