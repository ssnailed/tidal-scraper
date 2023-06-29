import json
from tidalapi import session, user, playlist, media, album, artist
from helper import CONF

ALBUM = 1
ARTIST = 2
PLAYLIST = 3
TRACK = 4



class account:
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
        self.favorites = user.Favorites(self.session, CONF['user_id'])
        self._state = {
            "albums": {},
            "artists": {},
            "playlists": {},
            "tracks": {},
        }

    @staticmethod
    def create_obj_state(
        obj: playlist.Playlist | media.Track | album.Album | artist.Artist,
        downloaded: bool = False,
    ) -> dict[str, int | bool]:

        match type(obj):
            case album.Album:
                obj_type = ALBUM
            case artist.Artist:
                obj_type = ARTIST
            case playlist.Playlist:
                obj_type = PLAYLIST
            case media.Track:
                obj_type = TRACK
            case _:
                raise Exception("Incorrect object type received")

        return {
            "id": obj.id,
            "type": obj_type,
            "downloaded": downloaded,
        }
