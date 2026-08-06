#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for user interfaces."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class UserInterfaceP(Protocol):
    """A user interface port."""
