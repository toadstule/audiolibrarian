#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Manage tags."""

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
