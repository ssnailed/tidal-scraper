#!/bin/python3
import tidalapi
import json
import sys
from datetime import datetime

config = tidalapi.Config(quality=tidalapi.Quality.lossless)
session = tidalapi.Session(config)

try:
    with open("auth.json", "rb") as f:
        a = json.load(f)
        a.expiry_time = datetime.strptime(a.expiry_time, "%y-%m-%d %H:%M:%S")
        session.load_oauth_session(
            a.token_type, a.access_token, a.refresh_token, a.expiry_time
        )
except (OSError, IndexError):
    session.login_oauth_simple()

if session.check_login():
    with open("auth.json", "w") as f:
        json.dump(
            {
                "token_type": session.token_type,
                "access_token": session.access_token,
                "refresh_token": session.refresh_token,
                "expiry_time": session.expiry_time,
            },
            f,
        )
else:
    sys.exit("Failed to log in")

user = session.get_user()
# albums = user.Favorites.albums()
# tracks = user.Favorites.tracks()
# artists = user.Favorites.artists()
#
# for album in albums:
#     if album.artist not in artists:
#         user.Favorites.add_artist(album.artist.id)
#
# for track in tracks:
#     if track.album not in albums:
#         user.Favorites.add_album(track.album.id)
