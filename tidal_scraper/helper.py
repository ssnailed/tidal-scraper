import re
import os
import tomllib
import sys
import traceback
from pprint import pp

extensions = [".flac", ".mp4", ".m4a", ""]
conf_text = """# All options postfixed "_dir" are expected to have a trailing slash!
skip_downloaded = true
error_log = "error.log"
# Quality can be one of "master, lossless, high and low"
# Keep in mind that you can only get the quality included in your tidal sub
quality = "lossless"
user_id =

dest_dir = "./downloads/"

# Leave empty for default state location 
# Default location is the first valid path in this order:
# XDG_STATE_HOME/tidal-scraper/
# XDG_CACHE_HOME/tidal-scraper/
# $HOME/.cache/tidal-scraper/
state_dir =

# These templates are passed their respective tidalapi objects
# Possible attributes can be found here: https://tidalapi.netlify.app/api.html
album_dir = "{album.artist.name}/{album.name}/"
playlist_dir = "{playlist.name}/"
# Track receives "albumartist" and "trackartist", but no "artist"
track_name = "{track.track_num}: {track.artist.name} - {track.name}"

# One of 160, 320, 480, 640, 750, 1080
playlist_image_size = 1080
# One of 80, 160, 320, 640, 1280
album_image_size = 1280
"""


def default_conf_file() -> str:
    home = os.getenv("HOME")
    assert home
    return (
        os.getenv("XDG_CONFIG_HOME") or home + "/.config"
    ) + "/tidal-scraper/conf.toml"


def default_state_file() -> str:
    home = os.getenv("HOME")
    assert home
    return (
        os.getenv("XDG_STATE_HOME")
        or os.getenv("XDG_CACHE_HOME")
        or home + "/.cache"
    ) + "/tidal-scraper/"

def write_conf(conf_file: str | None = None, notify: bool = False) -> None:
    if not conf_file:
        conf_file = default_conf_file()
    with open(conf_file, "w") as f:
        f.write(conf_text)
    if notify:
        print(f"Config file created at {conf_file}. Make sure to set your user ID!")

def get_conf(state_dir: str | None = None, conf_file: str | None = None) -> dict:
    if not conf_file:
        conf_file = default_conf_file()
    with open(conf_file, "rb") as f:
        conf = tomllib.load(f)

    if not state_dir:
        state_dir = default_state_file()

    conf["state_dir"] = state_dir

    return conf


def clean_template(path: str, **kwargs) -> str:
    path = os.path.expanduser(path)
    split = path.split("/")
    cleaned_split = [re.sub("/", " ", s.format(**kwargs)) for s in split]
    return "/".join(cleaned_split)


def log_error(logfile: str, template: str, **kwargs) -> None:
    with open(logfile, "a") as f:
        msg = template.format(**kwargs)
        f.write(msg + "\n")
        pp(traceback.format_exception(*sys.exc_info()), stream=f, indent=4)
        f.write("\n\n")
