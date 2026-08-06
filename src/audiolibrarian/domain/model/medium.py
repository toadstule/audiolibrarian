#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: medium."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from audiolibrarian.domain.model.record import Record

if TYPE_CHECKING:
    from audiolibrarian.domain.model import track, values
    from audiolibrarian.domain.model.record import ListF


@attrs.define(kw_only=True, frozen=True)
class Medium(Record):
    """A medium."""

    formats: ListF[str] | None = None
    titles: list[str] | None = None
    track_count: int | None = None
    tracks: dict[values.TrackNumber, track.Track] | None = None
