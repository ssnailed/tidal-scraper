#!/bin/sh
export USER_ID=188721652
export DL_PATH=/home/luca/Downloads
export DEST_PATH=/home/luca/Music
export AUTH_PATH=/home/luca/Secrets
export SKIP_DOWNLOADED=True
/bin/env python tidal_scrape.py
