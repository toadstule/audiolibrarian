"""Screen output utilities."""

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
import sys
from types import TracebackType


class Dots:
    """Context Manager that outputs a message, and dots...

    Example:
        with Dots("Please wait...") as d:
            for _ in range(10):
                time.sleep(1)  # or better, actually do some work here instead
                d.dot()
    """

    def __init__(self, message: str) -> None:
        """Initialize a Dots object."""
        self._out(message)

    def __enter__(self) -> "Dots":
        """Enter the context manager."""
        return self

    def __exit__(
        self,
        _: type[BaseException] | None,
        __: BaseException | None,
        ___: TracebackType | None,
    ) -> None:
        """Exit the context manager."""
        self._out("\n")

    def dot(self) -> None:
        """Output a dot."""
        self._out(".")

    @staticmethod
    def _out(message: str) -> None:
        sys.stdout.write(message)
        sys.stdout.flush()
