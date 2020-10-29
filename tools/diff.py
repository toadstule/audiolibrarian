#!/usr/bin/env python
import pprint
import sys

import mutagen

if __name__ == "__main__":
    assert len(sys.argv) == 3
    filename1, filename2 = sys.argv[1:3]

    song1 = mutagen.File(filename1)
    pprint.pp(sorted(song1.tags))

    song2 = mutagen.File(filename2)
    pprint.pp(sorted(song2.tags))

    pprint.pp(sorted(list(set(song1.tags) - set(song2.tags))))
    pprint.pp(sorted(list(set(song2.tags) - set(song1.tags))))
