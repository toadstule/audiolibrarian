#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for tag gateway."""

import pathlib
from typing import Protocol, Self, runtime_checkable

from audiolibrarian.domain.model import release


@runtime_checkable
class TagGatewayP(Protocol):
    """A tag gateway port."""

    filepath: pathlib.Path
    one_track: release.OneTrack

    @classmethod
    def factory(cls, filename: str | pathlib.Path) -> Self:
        """Construct a TagGateway instance (factory method)."""
        ...

    def extensions(self) -> set[str]:
        """Return the list of supported extensions."""
        ...

    def read_tags(self) -> release.OneTrack:
        """Read the tags from the audio file and return a populated OneTrack record."""
        ...

    def write_tags(self) -> None:
        """Write the tags to the audio file."""
        ...
