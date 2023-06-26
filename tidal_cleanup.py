#!/bin/env python
import tidalapi

USER_ID = 188721652

def idExists(objects: list, id: int) -> bool:
    for obj in objects:
        if obj.id == id:
            return True
    return False


config = tidalapi.Config(quality=tidalapi.Quality.lossless)
session = tidalapi.Session(config)
user = session.get_user(USER_ID)
favorites = tidalapi.user.Favorites(session, user.id)

existing_artists = favorites.artists()
existing_albums = favorites.albums()
existing_tracks = favorites.tracks()
for album in existing_albums:
    # ADD ARTIST
    print(album.artist.name, end=" ")
    if not idExists(existing_artists, album.artist.id):
        if favorites.add_artist(album.artist.id):
            print("added!")
        else:
            print("failed!")
        pass
    else:
        print("skipped!")
    # ADD TRACKS
    for track in album.tracks():
        print(track.name, end=" ")
        if not idExists(existing_tracks, track.id):
            if favorites.add_track(track.id):
                print("added!")
            else:
                print("failed!")
            pass
        else:
            print("skipped!")

existing_tracks = favorites.tracks()
for track in existing_tracks:
    print(track.album.name, end=" ")
    if not idExists(existing_albums, track.album.id):
        if favorites.add_album(track.album.id):
            print("added!")
        else:
            print("failed!")
    else:
        print("skipped!")
