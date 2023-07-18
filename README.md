# tidal-scraper

A simple command-line tool to download songs from tidal.

## Installation

```sh
pip install tidal-scraper
```

## Usage
Before using, execute `tidal-scraper -C` to write the configuration file. You will have to configure your user ID, which can be found in the last part of the URL of your tidal profile.

You run the script with one "Object" flag, which is one of `--album`, `--artist`, `--track` or `--playlist`, and one "Source" flag.
The source flag can either be `--favorite` or `--id`, which must be followed by the ID of the object you are trying to download.
You can find the ID in the URL of the album/track/artist e.g. "296153229" in "https://listen.tidal.com/album/296153229"

In addition to this, you can use `--config` to specify what configuration file to use and `--state` to specify a directory to keep state files in.
The state directory will contain a token file called 'auth.json' used to log into your tidal account. Keep this safe and do not share it!

## Use at Your Own Risk!
I will not be liable to you or anyone else for the loss of your tidal account as the result of using this script! While I have extensively tested it without any problems whatsoever, I cannot guarantee that your account will not be banned or otherwise impacted.
