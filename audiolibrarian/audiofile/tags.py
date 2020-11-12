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

# noinspection PyMissingConstructor
class Tags(dict):
    """A dict-like object that silently drops keys with None in their values.

    A key will be dropped if:
    * its value is None
    * its value is a list containing None
    * its value is a dict with None in its values
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __setitem__(self, k, v):
        if not (
            v is None
            or (type(v) is list and (None in v or "None" in v))
            or (type(v) is dict and (None in v.values() or "None" in v.values()))
        ):
            super().__setitem__(k, v)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
