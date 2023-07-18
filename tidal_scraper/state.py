from tidal_scraper.helper import log_error

import json
from datetime import datetime
from tidalapi import session, user, playlist, media, album, artist, Quality


class State:
    def __init__(
        self,
        conf: dict | None = None,
        state_dir: str | None = None,
        user_id: int | None = None,
        quality: str | None = None,
        errorfile: str | None = None,
    ):
        if conf is None:
            assert user_id is not None
            assert quality is not None
            assert state_dir is not None
            assert errorfile is not None
        else:
            user_id = user_id or conf["user_id"]
            quality = quality or conf["quality"]
            state_dir = state_dir or conf["state_dir"]
            errorfile = errorfile or conf["error_log"]

        match quality:
            case "master":
                q = Quality.master
            case "lossless":
                q = Quality.lossless
            case "high":
                q = Quality.high
            case "low":
                q = Quality.low
            case _:
                raise Exception("Bad Quality String")
        api_config = session.Config(quality=q)
        self.conf = conf
        self.user_id = user_id
        self.session = session.Session(api_config)
        self.favorites = user.Favorites(self.session, user_id)
        self.errorfile = errorfile
        self._state = {
            "albums": {},
            "artists": {},
            "playlists": {},
            "tracks": {},
        }

    def login(self, auth_file: str | None = None) -> None:
        s = self.session
        if auth_file is None:
            assert self.conf is not None
            auth_file = self.conf["state_dir"] + "auth.json"
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
        except (FileNotFoundError, IndexError, AssertionError):
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
                    json.dump(data, fp=f, indent=4)

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
                raise Exception("Object of incorrect type received")

        self._state[t][obj.id] = downloaded

    def state_downloaded(
        self, obj: playlist.Playlist | media.Track | album.Album | artist.Artist
    ) -> bool:
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
                raise Exception("Object of incorrect type received")
        return self._state[t].get(str(obj.id), False)

    def write_dl_state(self, statefile: str) -> None:
        with open(statefile, "w") as f:
            json.dump(self._state, fp=f, indent=4)

    def load_dl_state(self, state_file: str) -> None:
        try:
            with open(state_file, "r") as f:
                self._state = json.load(f)

            for t in self._state.values():
                for k, v in t.items():
                    assert isinstance(k, (str, type(None)))
                    assert isinstance(v, (bool, type(None)))
        except (FileNotFoundError, IndexError, KeyError):
            log_error(
                self.errorfile or "error.log",
                f"Could not find state file at {state_file}",
            )
        except (json.decoder.JSONDecodeError, AssertionError):
            log_error(
                self.errorfile or "error.log",
                f"Statefile at {state_file} is malformed",
            )
