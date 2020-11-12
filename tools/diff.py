#!/usr/bin/env python

# Copyright (C) 2020 Stephen Jibson
#
# This file is part of AudioLibrarian.
#
# AudioLibrarian is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# AudioLibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Foobar.  If not, see
# <https://www.gnu.org/licenses/>.
#

import pprint
import sys

import mutagen

if __name__ == "__main__":
    assert len(sys.argv) == 3
    filename1, filename2 = sys.argv[1:3]

    song1 = mutagen.File(filename1)
    pprint.pp(dict(song1.tags))

    song2 = mutagen.File(filename2)
    pprint.pp(dict(song2.tags))

    # pprint.pp(sorted(list(set(song1.tags) - set(song2.tags))))
    # pprint.pp(sorted(list(set(song2.tags) - set(song1.tags))))
    print(sorted(list(set(song1.tags) - set(song2.tags))))
    print(sorted(list(set(song2.tags) - set(song1.tags))))
