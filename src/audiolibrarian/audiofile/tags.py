"""Manage tags."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
from typing import Any


# noinspection PyMissingConstructor
class Tags(dict[Any, Any]):
    """A dict-like object that silently drops keys with None in their values.

    A key will be dropped if:
    * its value is None
    * its value is a list containing None
    * its value is a dict with None in its values
    """

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """Initialize a Tags object."""
        self.update(*args, **kwargs)

    def __setitem__(self, k: Any, v: Any) -> None:  # noqa: ANN401
        """Set an item only if it should not be dropped."""
        if not (
            v is None
            or (isinstance(v, list) and (None in v or "None" in v))
            or (isinstance(v, dict) and (None in v.values() or "None" in v.values()))
        ):
            super().__setitem__(k, v)

    def update(self, *args: Any, **kwargs: Any) -> None:  # noqa: ANN401
        """See base class."""
        for key, value in dict(*args, **kwargs).items():
            self[key] = value
