#!/bin/sh
path='scrape_pyenv'
python3 -m venv scrape_pyenv
./scrape_pyenv/bin/pip install -r requirements.txt
