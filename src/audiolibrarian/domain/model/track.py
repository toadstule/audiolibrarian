#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: track."""

import attrs

from audiolibrarian import text
from audiolibrarian.domain.model import values
from audiolibrarian.domain.model.record import ListF, Record


@attrs.define(kw_only=True)
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

    def get_filename(self, suffix: str = "") -> str:
        """Return a sane filename based on track number and title.

        If suffix is included, it will be appended to the filename.
        """
        if self.title is None or self.track_number is None:
            msg = "Unable to generate a filename for Track with missing number and/or title"
            raise ValueError(msg)
        return f"{self.track_number}__{text.filename_from_title(self.title)}{suffix}"
