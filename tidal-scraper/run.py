#!/bin/env python
from download import download_album
from state import State
from helper import CONF

s = State(CONF['user_id'], CONF['quality'])

s.login()

albums = s.favorites.albums()

download_album(albums[0])
s.set_dl_state(albums[0], True)
s.write_state()
