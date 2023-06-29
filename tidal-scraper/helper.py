import re
import tomllib
import sys
import traceback

with open("../config.toml", "rb") as conf:
    CONF = tomllib.load(conf)

EXTENSIONS = ['.flac', '.mp4', '.m4a', '']

def clean_template(path: str, **kwargs) -> str:
    split = path.split("/")
    cleaned_split = [re.sub("/", " ", s.format(**kwargs)) for s in split]
    return "/".join(cleaned_split)

def log_error(template: str, **kwargs):
    with open(CONF['error_log']) as f:
        error = template.format(**kwargs)
        f.write(error)
        traceback.print_exception(*sys.exc_info(), file=f)
