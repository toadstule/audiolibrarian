#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: track."""

import attrs

from audiolibrarian.domain.model import values
from audiolibrarian.domain.model.record import ListF, Record


@attrs.define(kw_only=True, frozen=True)
class Track(Record):
    """A track."""

    artist: str | None = None
    artists: ListF[str] | None = None
    artists_sort: list[str] | None = None
    file_info: values.FileInfo | None = None
    isrcs: list[str] | None = None
    musicbrainz_artist_ids: ListF[str] | None = None
    musicbrainz_release_track_id: str | None = None
    musicbrainz_track_id: str | None = None
    title: str | None = None
    track_number: values.TrackNumber | None = None
