import json
from datetime import datetime
from tidalapi import session, user, playlist, media, album, artist
from helper import CONF


class State:
    def __init__(self, user_id: int, quality: str):
        match quality:
            case "master":
                q = session.Quality.master
            case "lossless":
                q = session.Quality.lossless
            case "high":
                q = session.Quality.high
            case "low":
                q = session.Quality.low
            case _:
                raise Exception("Quality misconfigured in conf.toml")
        config = session.Config(quality=q)
        self.user_id = user_id
        self.session = session.Session(config)
        self.favorites = user.Favorites(self.session, CONF["user_id"])
        self._state = {
            "albums": {},
            "artists": {},
            "playlists": {},
            "tracks": {},
        }

    def login(self, auth_file: str | None = CONF["state_dir"] + "auth.json") -> None:
        s = self.session
        try:
            assert auth_file
            with open(auth_file, "r") as f:
                a = json.load(f)
                s.load_oauth_session(
                    a["token_type"],
                    a["access_token"],
                    a["refresh_token"],
                    datetime.fromtimestamp(a["expiry_time"]),
                )
        except (OSError, IndexError, AssertionError):
            s.login_oauth_simple()
            if (
                s.token_type
                and s.access_token
                and s.refresh_token
                and s.expiry_time
                and auth_file
            ):
                data = {
                    "token_type": s.token_type,
                    "access_token": s.access_token,
                    "refresh_token": s.refresh_token,
                    "expiry_time": s.expiry_time.timestamp(),
                }
                with open(auth_file, "w") as f:
                    json.dump(data, f)

        assert self.session.check_login()

    def set_dl_state(
        self,
        obj: playlist.Playlist | media.Track | album.Album | artist.Artist,
        downloaded: bool,
    ) -> None:
        match type(obj):
            case album.Album:
                t = "albums"
            case artist.Artist:
                t = "artists"
            case playlist.Playlist:
                t = "playlists"
            case media.Track:
                t = "tracks"
            case _:
                raise Exception("Incorrect object type received")

        self._state[t][obj.id] = downloaded

    def write_state(
        self, state_file_path: str = CONF["state_dir"] + "state.json"
    ) -> None:
        with open(state_file_path, "w") as f:
            json.dump(self._state, f)

    def load_state(
        self, state_file_path: str = CONF["state_dir"] + "state.json"
    ) -> None:
        with open(state_file_path, "r") as f:
            self._state = json.load(f)
