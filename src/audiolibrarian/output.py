#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Screen output utilities."""

import sys
from types import TracebackType
from typing import Self


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

    def __enter__(self) -> Self:
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
