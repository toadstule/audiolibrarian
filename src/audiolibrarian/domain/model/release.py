#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: release."""

from __future__ import annotations

from typing import TYPE_CHECKING

import attrs

from audiolibrarian.domain.model.record import Record

if TYPE_CHECKING:
    from audiolibrarian.domain.model import enums, values
    from audiolibrarian.domain.model.medium import Medium
    from audiolibrarian.domain.model.record import ListF
    from audiolibrarian.domain.model.track import Track


@attrs.define(kw_only=True, frozen=True)
class Release(Record):
    """A release."""

    album: str | None = None
    album_artists: ListF[str] | None = None
    album_artists_sort: ListF[str] | None = None
    asins: list[str] | None = None
    barcodes: list[str] | None = None
    catalog_numbers: list[str] | None = None
    date: str | None = None
    front_cover: values.FrontCover | None = None
    genres: ListF[str] | None = None
    labels: list[str] | None = None
    media: dict[int, Medium] | None = None
    medium_count: int | None = None
    musicbrainz_album_artist_ids: ListF[str] | None = None
    musicbrainz_album_id: str | None = None
    musicbrainz_release_group_id: str | None = None
    original_date: str | None = None
    original_year: str | None = None
    people: values.People | None = None
    release_countries: list[str] | None = None
    release_statuses: list[str] | None = None
    release_types: list[str] | None = None
    script: str | None = None
    source: enums.Source | None = None

    def pp(self, medium_number: int) -> str:
        """Return a string summary of the Release."""
        if self.media is None:
            msg = "Missing release information"
            raise ValueError(msg)
        medium_obj = self.media.get(medium_number)
        if medium_obj is None or medium_obj.tracks is None:
            tracks = "  (no tracks)"
        else:
            tracks = "\n".join(
                (
                    f"  {str(n).zfill(2)}: {t.title}"
                    for n, t in sorted(medium_obj.tracks.items(), key=lambda x: x[0].value)
                )
            )
        return "\n".join(
            (
                f"Album: {self.album}",
                f"Artist(s): {', '.join(self.album_artists) if self.album_artists else ''}",
                f"Medium: {medium_number} of {self.medium_count}",
                "Tracks:",
                tracks,
            )
        )


@attrs.define(kw_only=True, frozen=True)
class OneTrack(Record):
    """A single track."""

    release: Release | None = None
    medium_position: values.MediumPosition | None = None
    track_number: values.TrackNumber | None = None

    @property
    def medium(self) -> Medium | None:
        """Return the Medium object (or None)."""
        if self.release and self.release.media and self.medium_position:
            return self.release.media[self.medium_position.number]
        return None

    @property
    def track(self) -> Track | None:
        """Return the Track object (or None)."""
        if self.medium and self.medium.tracks:
            return self.medium.tracks[self.track_number]
        return None
