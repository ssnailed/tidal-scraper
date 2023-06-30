import re
import os
import toml
# TODO: wait for python to update to 3.11 for ubuntu users
# import tomllib
import sys
import traceback

extensions = [".flac", ".mp4", ".m4a", ""]

home = os.getenv("HOME")
state_dir = os.getenv("XDG_STATE_HOME") or os.getenv("XDG_CACHE_HOME")
conf_dir = os.getenv("XDG_CONFIG_HOME")
if not state_dir:
    assert home
    state_dir = home + "/.cache"

if not conf_dir:
    assert home
    conf_dir = home + "/.config"
conf_dir += "/tidal-scraper"
state_dir += "/tidal-scraper"

with open(conf_dir + "/conf.toml", "r") as f:
    conf = toml.load(f)
# with open(conf_dir + "/conf.toml", "rb") as f:
    # conf = tomllib.load(f)


def clean_template(path: str, **kwargs) -> str:
    path = os.path.expanduser(path)
    split = path.split("/")
    cleaned_split = [re.sub("/", " ", s.format(**kwargs)) for s in split]
    return "/".join(cleaned_split)


def log_error(template: str, **kwargs):
    with open(conf["error_log"], "a") as f:
        msg = template.format(**kwargs)
        f.write(msg + "\n")
        traceback.format_exception(*sys.exc_info())
        f.write("\n\n")
