#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: record."""

from __future__ import annotations

from typing import Any

import attrs


class ListF[T](list[T]):
    """A list, with a first property."""

    @property
    def first(self) -> T | None:
        """Return the first element in the list (or None, if the list is empty)."""
        return self[0] if self else None


@attrs.define
class Record:
    """Base class for records.

    Overrides true/false test for records returning false if all fields are None.
    """

    def __bool__(self) -> bool:
        """Return a boolean representation of the Record."""
        return any(x is not None for x in attrs.asdict(self, recurse=False).values())

    def asdict(self) -> dict[Any, Any]:
        """Return a dict version of the record."""
        return attrs.asdict(self)
