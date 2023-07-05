from tidalapi import Album, Track, Artist, Playlist
from tidal_scraper.download import (
    download_album,
    download_playlist,
    download_track,
    download_artist,
)
from tidal_scraper.state import State
from tidal_scraper.helper import get_conf, human_sleep
from argparse import ArgumentParser, Namespace
from pathlib import Path


def handle_favorites(state: State, conf: dict, args: Namespace) -> None:
    match args.obj:
        case "album":
            for album in state.favorites.albums():
                download_album(album, conf)
                human_sleep()
        case "track":
            for track in state.favorites.tracks():
                download_track(track, conf)
                human_sleep()
        case "artist":
            for artist in state.favorites.artists():
                download_artist(artist, conf)
                human_sleep()
        case "playlist":
            for playlist in state.favorites.playlists():
                download_playlist(playlist, conf)
                human_sleep()


def handle_id(state: State, conf: dict, args: Namespace) -> None:
    match args.obj:
        case "album":
            album = Album(state.session, args.id)
            download_album(album, conf)
        case "track":
            track = Track(state.session, args.id)
            download_track(track, conf)
        case "artist":
            artist = Artist(state.session, args.id)
            download_artist(artist, conf)
        case "playlist":
            playlist = Playlist(state.session, args.id)
            download_playlist(playlist, conf)


def run():
    parser = ArgumentParser(prog="tidal-scraper", description="Tidal music downloader")
    parser.add_argument(
        "-c", "--config", help="Configuration file to use", type=Path, dest="conf_file"
    )
    parser.add_argument(
        "-s", "--state", help="Directory to keep state in", type=Path, dest="state_dir"
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

    conf = get_conf(args.state_dir, args.conf_file)
    state = State(conf["user_id"], conf["quality"], conf["state_dir"])
    state.login(conf["state_dir"] + "auth.json")

    if args.favorite:
        handle_favorites(state, conf, args)
    elif args.id is not None:
        handle_id(state, conf, args)

    state.write_dl_state(conf["state_dir"] + "state.json")
