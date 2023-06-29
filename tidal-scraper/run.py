#!/bin/env python
from download import download_album
from state import State
from helper import conf

s = State(conf['user_id'], conf['quality'])
s.login()
albums = s.favorites.albums()

try:
    s.load_dl_state
except:
    pass

download_album(albums[0])
s.set_dl_state(albums[0], True)
s.write_dl_state()
