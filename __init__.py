from scraper import scraper
import os

authfile = os.environ["XDG_CACHE_HOME"] + "/auth.json"
s = scraper(authfile)
