#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Common user input functions."""

from __future__ import annotations

import sys
from typing import Final

from audiolibrarian.common import text

TERMINAL_BELL: Final[str] = "\a"


def _beep() -> None:
    """Sound a terminal bell."""
    sys.stdout.write(TERMINAL_BELL)  # Terminal bell escape char.
    sys.stdout.flush()


def input_int(prompt: str, *, min_: int | None = None, max_: int | None = None) -> int:
    """Prompt the user for an integer value.

    Args:
        prompt: The prompt to display.
        min_: The (optional) minimum value.
        max_: The (optional) maximum value.
    """
    while True:
        try:
            response = int(input_str(prompt))
        except ValueError:
            continue
        if (min_ is None or response >= min_) and (max_ is None or response <= max_):
            return int(response)
    return 0


def input_str(prompt: str) -> str:
    """Sound a terminal bell then prompt the user for input."""
    _beep()
    return input(prompt)


def input_uuid(prompt: str) -> str:
    """Prompt for, and return a UUID."""
    while True:
        if (uuid := text.get_uuid(input_str(prompt))) is not None:
            return uuid
