"""Record (dataclass) definitions.

Useful field reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py
"""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
import dataclasses
import enum
import pathlib
from typing import Any

from audiolibrarian import text


class BitrateMode(enum.Enum):
    """Bitrate modes."""

    UNKNOWN = 0
    CBR = 1
    VBR = 2


class FileType(enum.Enum):
    """Audio file types."""

    UNKNOWN = 0
    AAC = 1
    FLAC = 2
    MP3 = 3
    WAV = 4


class Source(enum.Enum):
    """Information source."""

    MUSICBRAINZ = 1
    TAGS = 2


class ListF(list[Any]):
    """A list, with a first property."""

    @property
    def first(self) -> Any | None:  # noqa: ANN401
        """Return the first element in the list (or None, if the list is empty)."""
        return self[0] if self else None


@dataclasses.dataclass(kw_only=True)
class Record:
    """Base class for records.

    Overrides true/false test for records returning false if all fields are None.
    """

    def __bool__(self) -> bool:
        """Return a boolean representation of the Record."""
        return bool([x for x in dataclasses.asdict(self).values() if x is not None])

    def asdict(self) -> dict[Any, Any]:
        """Return a dict version of the record."""
        return dataclasses.asdict(self)


# Primitive Record Types
@dataclasses.dataclass(kw_only=True)
class FileInfo(Record):
    """File information."""

    bitrate: int | None = None
    bitrate_mode: BitrateMode | None = None
    path: pathlib.Path | None = None
    type: FileType | None = None


@dataclasses.dataclass(kw_only=True)
class FrontCover(Record):
    """A front cover."""

    data: bytes | None = None
    desc: str | None = None
    mime: str | None = None


@dataclasses.dataclass(kw_only=True)
class Performer(Record):
    """A performer with an instrument."""

    name: str | None = None
    instrument: str | None = None


@dataclasses.dataclass(kw_only=True)
class Track(Record):
    """A track."""

    artist: str | None = None
    artists: ListF | None = None
    artists_sort: list[str] | None = None
    file_info: FileInfo | None = None
    isrcs: list[str] | None = None
    musicbrainz_artist_ids: ListF | None = None
    musicbrainz_release_track_id: str | None = None
    musicbrainz_track_id: str | None = None
    title: str | None = None
    track_number: int | None = None

    def get_filename(self, suffix: str = "") -> str:
        """Return a sane filename based on track number and title.

        If suffix is included, it will be appended to the filename.
        """
        if self.title is None or self.track_number is None:
            msg = "Unable to generate a filename for Track with missing number and/or title"
            raise ValueError(msg)
        return (
            str(self.track_number).zfill(2) + "__" + text.filename_from_title(self.title) + suffix
        )


# Combined Record Types (fields + other record types)
@dataclasses.dataclass(kw_only=True)
class Medium(Record):
    """A medium."""

    formats: ListF | None = None
    titles: list[str] | None = None
    track_count: int | None = None
    tracks: dict[int, Track] | None = None


@dataclasses.dataclass(kw_only=True)
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


@dataclasses.dataclass(kw_only=True)
class Release(Record):
    """A release."""

    album: str | None = None
    album_artists: ListF | None = None
    album_artists_sort: ListF | None = None
    asins: list[str] | None = None
    barcodes: list[str] | None = None
    catalog_numbers: list[str] | None = None
    date: str | None = None
    front_cover: FrontCover | None = dataclasses.field(default=None, repr=False)
    genres: ListF | None = None
    labels: list[str] | None = None
    media: dict[int, Medium] | None = None
    medium_count: int | None = None
    musicbrainz_album_artist_ids: ListF | None = None
    musicbrainz_album_id: str | None = None
    musicbrainz_release_group_id: str | None = None
    original_date: str | None = None
    original_year: str | None = None
    people: People | None = None
    release_countries: list[str] | None = None
    release_statuses: list[str] | None = None
    release_types: list[str] | None = None
    script: str | None = None
    source: Source | None = None

    def get_artist_album_path(self) -> pathlib.Path:
        """Return a directory for the artist/album/disc combination.

        Example:
          -  artist__the/1969__the_album
        """
        if self.album_artists_sort is None or self.album_artists_sort.first is None:
            msg = "Unable to determine artist path without artist(s)"
            raise ValueError(msg)
        artist_dir = pathlib.Path(text.filename_from_title(self.album_artists_sort.first))
        if self.original_year is None or self.album is None:
            msg = "Unable to determine album path without year and album"
            raise ValueError(msg)
        album_dir = pathlib.Path(text.filename_from_title(f"{self.original_year}__{self.album}"))
        return artist_dir / album_dir

    def pp(self, medium_number: int) -> str:
        """Return a string summary of the Release."""
        if self.media is None:
            msg = "Missing release information"
            raise ValueError(msg)
        tracks = "\n".join(
            (
                f"  {str(n).zfill(2)}: {t.title}"
                for n, t in sorted(self.media[medium_number].tracks.items())
            )
        )
        return "\n".join(
            (
                f"Album: {self.album}",
                f"Artist(s): {', '.join(self.album_artists)}",
                f"Medium: {medium_number} of {self.medium_count}",
                "Tracks:",
                tracks,
            )
        )


@dataclasses.dataclass(kw_only=True)
class OneTrack(Record):
    """A single track."""

    release: Release | None = None
    medium_number: int | None = None
    track_number: int | None = None

    @property
    def medium(self) -> Medium | None:
        """Return the Medium object (or None)."""
        if self.release and self.release.media:
            return self.release.media[self.medium_number]
        return None

    @property
    def track(self) -> Track | None:
        """Return the Track object (or None)."""
        if self.medium and self.medium.tracks:
            return self.medium.tracks[self.track_number]
        return None

    def get_artist_album_disc_path(self) -> pathlib.Path:
        """Return a directory for the artist/album/disc combination.

        Example:
          - artist__the/1969__the_album
          - artist__the/1969__the_album/disc2
        """
        if (self.medium_number, self.release.medium_count) == (1, 1):
            return self.release.get_artist_album_path()
        return self.release.get_artist_album_path() / f"disc{self.medium_number}"
