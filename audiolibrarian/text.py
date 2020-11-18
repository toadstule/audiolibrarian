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

import re
import sys
from typing import List

from audiolibrarian.picard_src import (
    replace_non_ascii,
    unicode_simplify_combinations,
    unicode_simplify_compatibility,
    unicode_simplify_punctuation,
)

digit_regex = re.compile(r"([0-9]+)")
uuid_regex = re.compile(r"[a-f0-9]{8}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{4}-?[a-f0-9]{12}", re.I)


def alpha_numeric_key(x):
    """A key that can be used for sorting alpha-numeric strings numerically.

    Example:
        from audiolibrarian.text import alpha_numeric_key

        l = ["8__eight", "7__seven", "10__ten", "11__eleven"]
        sorted(l)
        # ['10__ten', '11__eleven', '7__seven', '8__eight']
        sorted(l, key=alpha_numeric_key)
        # ['7__seven', '8__eight', '10__ten', '11__eleven']
    """
    return [int(x) if x.isdigit() else x for x in digit_regex.split(str(x))]


def join(strings: List[str], joiner: str = ", ", word: str = "and") -> str:
    if not strings:
        return ""
    if len(strings) == 1:
        return strings[0]
    return joiner.join(strings[:-1]) + " " + word + " " + strings[-1]


def fix(text: str) -> str:
    """Replace some special characters."""
    text = unicode_simplify_combinations(text)
    # text = unicode_simplify_accents(text)
    text = unicode_simplify_punctuation(text)
    text = unicode_simplify_compatibility(text)
    return text


def get_filename(title: str) -> str:
    """Convert a title into a filename."""
    # allowed_chars = string.ascii_letters + string.digits + "_.,"
    escape_required = "'!\"#$&'()*;<>?[]\\`{}|~\t\n); "
    invalid = "/"
    no_underscore_replace = "'!\""
    result = []
    for ch in replace_non_ascii(title):
        if ch == "&":
            result.extend("and")
        elif ch.isascii() and ch not in escape_required and ch not in invalid:
            result.append(ch)
        elif ch not in no_underscore_replace:
            result.append("_")
    result = "".join(result).rstrip("_")
    # strip tailing dots, unless we end with an upper-case letter, then put one dot back
    if result.endswith(".") and result.rstrip(".")[-1].isupper():
        return result.rstrip(".") + "."
    return result.rstrip(".")


def get_numbers(text: str) -> List[int]:
    """Get a list of all the numbers in the given string."""
    return [int(x) for x in digit_regex.findall(text)]


def get_track_number(filename: str) -> int:
    """Get a track number from a filename or from the user."""

    if n := get_numbers(filename):
        return n[0]
    while True:
        try:
            return int(input_(f"Enter the track number for: {filename}"))
        except ValueError:
            pass


def get_uuid(text: str) -> (str, None):
    """Return the first UUID found within a given string."""
    match = uuid_regex.search(text)
    if match is not None:
        return match.group()


def input_(prompt: str) -> str:
    # terminal bell
    sys.stdout.write("\a")
    sys.stdout.flush()
    return input(prompt)
