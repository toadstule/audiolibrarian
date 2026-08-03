#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Show differences in tags between two files."""

import pprint
import sys

import mutagen

if __name__ == "__main__":
    assert len(sys.argv) == 3  # noqa: S101, PLR2004
    filename1, filename2 = sys.argv[1:3]

    song1 = mutagen.File(filename1)
    pprint.pp(dict(song1.tags))

    song2 = mutagen.File(filename2)
    pprint.pp(dict(song2.tags))

    # pprint.pp(sorted(list(set(song1.tags) - set(song2.tags))))  # noqa: ERA001
    # pprint.pp(sorted(list(set(song2.tags) - set(song1.tags))))  # noqa: ERA001
    print(sorted(set(song1.tags) - set(song2.tags)))
    print(sorted(set(song2.tags) - set(song1.tags)))
