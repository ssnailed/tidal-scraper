from tidal_scraper.state import State
from tidal_scraper.helper import get_conf, write_conf
from tidal_scraper.download import (
    download_album,
    download_playlist,
    download_track,
    download_artist,
)

import sys
from tidalapi import Album, Track, Artist, Playlist
from argparse import ArgumentParser, Namespace
from pathlib import Path


def save_state(
    state: State, obj: Playlist | Track | Album | Artist, state_file: str
) -> None:
    state.set_dl_state(obj, True)
    state.write_dl_state(state_file)


def handle_favorites(state: State, conf: dict, args: Namespace) -> None:
    match args.obj:
        case "album":
            for album in state.favorites.albums():
                if not state.state_downloaded(album):
                    download_album(album, conf)
                    save_state(state, album, conf["state_dir"] + "/state.json")
        case "track":
            for track in state.favorites.tracks():
                if not state.state_downloaded(track):
                    download_track(track, True, conf)
                    save_state(state, track, conf["state_dir"] + "/state.json")
        case "artist":
            for artist in state.favorites.artists():
                if not state.state_downloaded(artist):
                    download_artist(artist, conf)
                    save_state(state, artist, conf["state_dir"] + "/state.json")
        case "playlist":
            for playlist in state.favorites.playlists():
                if not state.state_downloaded(playlist):
                    download_playlist(playlist, conf)
                    save_state(state, playlist, conf["state_dir"] + "/state.json")


def handle_id(state: State, conf: dict, args: Namespace) -> None:
    match args.obj:
        case "album":
            album = Album(state.session, args.id)
            download_album(album, conf)
            state.set_dl_state(album, True)
        case "track":
            track = Track(state.session, args.id)
            download_track(track, False, conf)
            state.set_dl_state(track, True)
        case "artist":
            artist = Artist(state.session, args.id)
            download_artist(artist, conf)
            state.set_dl_state(artist, True)
        case "playlist":
            playlist = Playlist(state.session, args.id)
            download_playlist(playlist, conf)
            state.set_dl_state(playlist, True)


def run():
    parser = ArgumentParser(prog="tidal-scraper", description="Tidal music downloader")
    parser.add_argument(
        "-c", "--config", help="Configuration file to use", type=Path, dest="conf_file"
    )
    parser.add_argument(
        "-s", "--state", help="Directory to keep state in", type=Path, dest="state_dir"
    )
    parser.add_argument(
        "-C",
        "--create-conf",
        action="store_true",
        help="Create config file and exit",
        dest="create_conf",
    )
    obj = parser.add_mutually_exclusive_group(required=True)
    obj.add_argument(
        "-a",
        "--album",
        action="store_const",
        const="album",
        help="Download an album",
        dest="obj",
    )
    obj.add_argument(
        "-A",
        "--artist",
        action="store_const",
        const="artist",
        help="Download an artist's albums",
        dest="obj",
    )
    obj.add_argument(
        "-p",
        "--playlist",
        action="store_const",
        const="playlist",
        help="Download a playlist",
        dest="obj",
    )
    obj.add_argument(
        "-t",
        "--track",
        action="store_const",
        const="track",
        help="Download a single track",
        dest="obj",
    )
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument(
        "-f",
        "--favorite",
        action="store_true",
        help="Download all favorited",
        dest="favorite",
    )
    source.add_argument(
        "-i",
        "--id",
        type=int,
        help="Download by ID",
        dest="id",
    )
    args = parser.parse_args()

    try:
        conf = get_conf(args.state_dir, args.conf_file)
    except FileNotFoundError:
        write_conf(notify=True)
        sys.exit()

    state = State(conf)
    state.load_dl_state(conf["state_dir"] + "state.json")
    state.login()

    try:
        if args.create_conf:
            write_conf(notify=True)
        elif args.favorite:
            handle_favorites(state, conf, args)
        elif args.id is not None:
            handle_id(state, conf, args)
    except KeyboardInterrupt:
        print("Bye bye! Come back again!")
