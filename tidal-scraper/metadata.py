from typing import BinaryIO
from mutagen import flac, mp4  # , mp3

from mutagen.mp4 import MP4Tags
from mutagen._vorbis import VCommentDict

# from mutagen.id3._tags import ID3Tags

# from mutagen.id3._frames import (
#     APIC,
#     TALB,
#     TCOP,
#     TDRC,
#     TIT2,
#     TPE1,
#     TRCK,
#     TOPE,
#     TCON,
#     TCOM,
#     TSRC,
#     USLT,
# )


def __write_flac(file: flac.FLAC, **kwargs) -> None:
    tags = VCommentDict()
    tags["title"] = kwargs["title"]
    tags["album"] = kwargs["album"]
    # There doesn't seem to be a standard way of listing multiple artists in an ID3 tag
    # This method seems to be the most widely recognized
    tags["albumartist"] = "; ".join(kwargs["albumartist"])
    tags["artist"] = "; ".join(kwargs["artist"])
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


# def __write_mp3(file: mp3.MP3, **kwargs) -> None:
#     tags = ID3Tags()
#     tags.add(TIT2(encoding=3, text=kwargs["title"]))
#     tags.add(TALB(encoding=3, text=kwargs["album"]))
#     tags.add(TOPE(encoding=3, text=kwargs["albumartist"]))
#     tags.add(TPE1(encoding=3, text=kwargs["artist"]))
#     tags.add(TCOP(encoding=3, text=kwargs["copyright"]))
#     tags.add(TRCK(encoding=3, text=kwargs["tracknumber"]))
#     tags.add(TCON(encoding=3, text=kwargs["genre"]))
#     tags.add(TDRC(encoding=3, text=kwargs["date"]))
#     tags.add(TCOM(encoding=3, text=kwargs["composer"]))
#     tags.add(TSRC(encoding=3, text=kwargs["isrc"]))
#     tags.add(USLT(encoding=3, text=kwargs["lyrics"]))
#     tags.add(APIC(encoding=3, data=kwargs["cover"], mime=kwargs["cover_mime"]))
#
#     match kwargs['cover_mime']:
#         case 'image/jpeg':
#             fmt = mp4.AtomDataType(13)
#         case 'image/png':
#             fmt = mp4.AtomDataType(14)
#         case _:
#             fmt = None
#
#     if fmt is not None:
#         pic = mp4.MP4Cover(kwargs['cover'])
#         pic.imageformat = fmt
#
#     file.tags = tags
#     file.save()


def write(
    fp: BinaryIO,
    codec: str,
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
):
    args = locals()
    # TODO: Figure out what codecs are sent in the manifest
    # WARN: This match is currently using placeholders
    match codec:
        case "???flac???":
            file = flac.FLAC(fp)
            __write_flac(file, *args)
        case "???aac???":
            file = mp4.MP4(fp)
            __write_mp4(file, *args)
