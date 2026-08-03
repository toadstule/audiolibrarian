#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Show tags."""

import pprint
import sys

import mutagen

if __name__ == "__main__":
    filename = sys.argv[1]

    song = mutagen.File(filename)
    if "covr" in song.tags:
        song.tags["covr"] = ""
    pprint.pp(dict(song.tags))
