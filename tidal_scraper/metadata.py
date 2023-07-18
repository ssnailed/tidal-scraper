from mutagen import flac, mp4
from mutagen.mp4 import MP4Tags
from mutagen._vorbis import VCommentDict
from typing import BinaryIO


def __write_flac(file: flac.FLAC, **kwargs) -> None:
    tags = VCommentDict()
    tags["title"] = kwargs["title"]
    tags["album"] = kwargs["album"]
    tags["albumartist"] = kwargs["albumartist"]
    tags["artist"] = kwargs["artist"]
    tags["copyright"] = kwargs["copyright"]
    tags["tracknumber"] = kwargs["tracknumber"]
    tags["tracktotal"] = kwargs["tracktotal"]
    tags["discnumber"] = kwargs["discnumber"]
    tags["disctotal"] = kwargs["disctotal"]
    tags["genre"] = kwargs["genre"]
    tags["date"] = kwargs["date"]
    tags["composer"] = kwargs["composer"]
    tags["isrc"] = kwargs["isrc"]
    tags["lyrics"] = kwargs["lyrics"]
    file.tags = tags

    pic = flac.Picture()
    pic.data = kwargs["cover"]
    pic.mime = kwargs["cover_mime"]
    file.clear_pictures()
    file.add_picture(pic)

    file.save()


def __write_mp4(file: mp4.MP4, **kwargs) -> None:
    tags = MP4Tags()
    tags["\xa9nam"] = kwargs["title"]
    tags["\xa9alb"] = kwargs["album"]
    tags["aART"] = kwargs["albumartist"]
    tags["\xa9ART"] = kwargs["artist"]
    tags["cprt"] = kwargs["copyright"]
    tags["trkn"] = [[kwargs["tracknumber"], kwargs["totaltrack"]]]
    tags["disk"] = [[kwargs["discnumber"], kwargs["totaldisc"]]]
    tags["\xa9gen"] = kwargs["genre"]
    tags["\xa9day"] = kwargs["date"]
    tags["\xa9wrt"] = kwargs["composer"]
    tags["\xa9lyr"] = kwargs["lyrics"]

    file.tags = tags
    file.save


def write(
    fp: BinaryIO,
    mime: str,
    title: str,
    album: str,
    tracknumber: str,
    tracktotal: str,
    discnumber: str = "",
    disctotal: str = "",
    artist: list[str] = [""],
    albumartist: list[str] = [""],
    genre: str = "",
    date: str = "",
    composer: str = "",
    isrc: str = "",
    lyrics: str = "",
    copyright: str = "",
    cover: bytes | None = None,
    cover_mime: str | None = None,
) -> None:
    args = locals()
    fp.seek(0)
    match mime:
        case "audio/flac":
            f = flac.FLAC(fp)
            __write_flac(f, *args)
        case "audio/mp4":
            f = mp4.MP4(fp)
            __write_mp4(f, *args)
        case _:
            raise Exception(f"Couldn't recognize mimetype {mime}")
