"""Text utilities."""

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
import pathlib
import re
import sys
from typing import Any

import picard_src

_DIGIT_REGEX = re.compile(r"([0-9]+)")
_UUID_REGEX = re.compile(
    r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}", re.IGNORECASE
)


def alpha_numeric_key(text: str | pathlib.Path) -> list[Any]:
    """Return a key that can be used for sorting alphanumeric strings numerically.

    Example:
        from audiolibrarian import text

        l = ["8__eight", "7__seven", "10__ten", "11__eleven"]
        sorted(l)
        # ['10__ten', '11__eleven', '7__seven', '8__eight']
        sorted(l, key=text.alpha_numeric_key)
        # ['7__seven', '8__eight', '10__ten', '11__eleven']
    """
    return [int(x) if x.isdigit() else x for x in _DIGIT_REGEX.split(str(text))]


def filename_from_title(title: str) -> str:
    """Convert a title into a filename."""
    escape_required = "'!\"#$&'()*;<>?[]\\`{}|~\t\n); "
    invalid = "/"
    no_underscore_replace = "'!\""
    results: list[str] = []
    for char in picard_src.replace_non_ascii(title):  # type: ignore[no-untyped-call]
        if char == "&":
            results.extend("and")
        elif char.isascii() and char not in escape_required and char not in invalid:
            results.append(char)
        elif char not in no_underscore_replace:
            results.append("_")
    result = "".join(results).rstrip("_")
    # Strip tailing dots, unless we end with an upper-case letter, then put one dot back.
    if result.endswith(".") and result.rstrip(".")[-1].isupper():
        return result.rstrip(".") + "."
    return result.rstrip(".")


def fix(text: str) -> str:
    """Replace some special characters."""
    text = picard_src.unicode_simplify_combinations(text)  # type: ignore[no-untyped-call]
    text = picard_src.unicode_simplify_punctuation(text)  # type: ignore[no-untyped-call]
    return picard_src.unicode_simplify_compatibility(text)  # type: ignore[no-untyped-call, no-any-return]


def get_numbers(text: str) -> list[int]:
    """Get a list of all the numbers in the given string."""
    return [int(x) for x in _DIGIT_REGEX.findall(text)]


def get_track_number(filename: str) -> int:
    """Get a track number from a filename or from the user."""
    if numbers := get_numbers(filename):
        return numbers[0]
    while True:  # pragma: no cover
        try:
            return int(input_(f"Enter the track number for: {filename}"))
        except ValueError:
            pass


def get_uuid(text: str) -> str | None:
    """Return the first UUID found within a given string."""
    if (match := _UUID_REGEX.search(text)) is not None:
        return match.group()
    return None


def input_(prompt: str) -> str:  # pragma: no cover
    """Sound a terminal bell then prompt the user for input."""
    sys.stdout.write("\a")  # Terminal bell escape char.
    sys.stdout.flush()
    return input(prompt)


def join(strings: list[str], joiner: str = ", ", word: str = "and") -> str:
    """Join string with joiner and word.

    Example:
        text.join(["eggs", "bacon", "spam"])
        # "eggs, bacon and spam"
    """
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]
    return joiner.join(strings[:-1]) + " " + word + " " + strings[-1]
