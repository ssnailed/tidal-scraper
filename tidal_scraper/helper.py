import re
import os
import time
import random

import tomllib
import sys
import traceback

extensions = [".flac", ".mp4", ".m4a", ""]


def get_conf(state_dir: str | None = None, conf_file: str | None = None) -> dict:
    home = os.getenv("HOME")
    assert home

    conf_file = (os.getenv("XDG_CONFIG_HOME") or home + "/.config") + "/tidal-scraper/conf.toml"
    with open(conf_file, "rb") as f:
        conf = tomllib.load(f)

    if not state_dir:
        state_dir = (
            os.getenv("XDG_STATE_HOME")
            or os.getenv("XDG_CACHE_HOME")
            or home + "/.cache"
        )
        state_dir += "/tidal-scraper"
        conf["state_dir"] = state_dir

    return conf


def clean_template(path: str, **kwargs) -> str:
    path = os.path.expanduser(path)
    split = path.split("/")
    cleaned_split = [re.sub("/", " ", s.format(**kwargs)) for s in split]
    return "/".join(cleaned_split)


def log_error(logfile: str, template: str, **kwargs):
    with open(logfile, "a") as f:
        msg = template.format(**kwargs)
        f.write(msg + "\n")
        traceback.format_exception(*sys.exc_info())
        f.write("\n\n")


def human_sleep() -> None:
    t = random.randrange(10, 50) / 10
    time.sleep(t)
