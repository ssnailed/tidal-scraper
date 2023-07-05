import json
from datetime import datetime
from tidalapi import session, user, playlist, media, album, artist


class State:
    def __init__(self, user_id: int, quality: str, dl_state_path: str):
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
                raise Exception("Bad Quality String")
        config = session.Config(quality=q)
        self.user_id = user_id
        self.session = session.Session(config)
        self.favorites = user.Favorites(self.session, user_id)
        try:
            self.load_dl_state(dl_state_path)
        except:
            self._state = {
                "albums": {},
                "artists": {},
                "playlists": {},
                "tracks": {},
            }

    def login(self, auth_file: str | None = None) -> None:
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

    def write_dl_state(self, statefile: str) -> None:
        with open(statefile, "w") as f:
            json.dump(self._state, f)

    def load_dl_state(self, statefile: str) -> None:
        with open(statefile, "r") as f:
            self._state = json.load(f)

        assert type(self._state["albums"]) is dict[int, bool]
        assert type(self._state["artists"]) is dict[int, bool]
        assert type(self._state["playlists"]) is dict[int, bool]
        assert type(self._state["tracks"]) is dict[int, bool]
