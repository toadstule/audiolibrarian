#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: value objects."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar

import attrs

from audiolibrarian.domain.model.record import Record

if TYPE_CHECKING:
    import pathlib

    from audiolibrarian.domain.model import enums


@attrs.define(kw_only=True, frozen=True)
class FileInfo(Record):
    """File information."""

    bitrate: int | None = None
    bitrate_mode: enums.BitrateMode | None = None
    path: pathlib.Path | None = None
    type: enums.FileType | None = None


@attrs.define(kw_only=True, frozen=True)
class FrontCover(Record):
    """A front cover."""

    data: bytes | None = None
    desc: str | None = None
    mime: str | None = None


@attrs.define(kw_only=True, frozen=True)
class MediumPosition(Record):
    """A disc position."""

    number: int = attrs.field(validator=attrs.validators.instance_of(int))
    count: int

    # noinspection unresolved-references
    @number.validator
    def _number_validator(self, attribute: attrs.Attribute[int], value: int) -> None:
        del attribute  # unused
        if not 1 <= value <= self.count:
            msg = f"number must be between 1 and count ({self.count})"
            raise ValueError(msg)


@attrs.define(kw_only=True, frozen=True)
class People(Record):
    """People."""

    arrangers: list[str] | None = None
    composers: list[str] | None = None
    conductors: list[str] | None = None
    engineers: list[str] | None = None
    lyricists: list[str] | None = None
    mixers: list[str] | None = None
    performers: list[Performer] | None = None
    producers: list[str] | None = None
    writers: list[str] | None = None


@attrs.define(kw_only=True, frozen=True)
class Performer(Record):
    """A performer with an instrument."""

    name: str | None = None
    instrument: str | None = None


@attrs.define(frozen=True)
class TrackNumber(Record):
    """A track number."""

    _DIGIT_COUNT: ClassVar[int] = 2

    value: int = attrs.field(validator=[attrs.validators.instance_of(int), attrs.validators.ge(0)])

    @classmethod
    def from_filename(cls, filename: str) -> TrackNumber:
        """Extract the track number from a filename."""
        return cls(value=int(filename.split("__", 1)[0]))

    def __str__(self) -> str:
        """Return the track number as a string, padded with zeros."""
        return str(self.value).zfill(TrackNumber._DIGIT_COUNT)
