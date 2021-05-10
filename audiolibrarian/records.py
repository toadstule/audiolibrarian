"""Record (dataclass) definitions."""

#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

# Useful field reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py

import dataclasses
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Optional

from audiolibrarian import text


class BitrateMode(Enum):
    """Bitrate modes."""

    UNKNOWN = 0
    CBR = 1
    VBR = 2


class FileType(Enum):
    """Audio file types."""

    UNKNOWN = 0
    AAC = 1
    FLAC = 2
    MP3 = 3
    WAV = 4


class Source(Enum):
    """Information source."""

    MUSICBRAINZ = 1
    TAGS = 2


class ListF(list):
    """A list, with a first property."""

    @property
    def first(self) -> Optional[Any]:
        """Return the first element in the list (or None, if the list is empty)."""
        if self:
            return self[0]
        return None


@dataclass
class Record:
    """Base class for records.

    Overrides true/false test for records returning false if all fields are None.
    """

    def __bool__(self):
        return bool([x for x in asdict(self).values() if x is not None])

    def asdict(self) -> dict:
        """Returns a dict version of the record."""
        return dataclasses.asdict(self)


# Primitive Record Types
@dataclass
class FileInfo(Record):
    """File information."""

    bitrate: int = None
    bitrate_mode: BitrateMode = None
    path: Path = None
    type: FileType = None


@dataclass
class FrontCover(Record):
    """A front cover."""

    data: bytes = None
    desc: str = None
    mime: str = None


@dataclass
class Performer(Record):
    """A performer with an instrument."""

    name: str = None
    instrument: str = None


@dataclass
class Track(Record):
    """A track."""

    artist: str = None
    artists: ListF = None
    artists_sort: list[str] = None
    file_info: FileInfo = None
    isrcs: list[str] = None
    musicbrainz_artist_ids: ListF = None
    musicbrainz_release_track_id: str = None
    musicbrainz_track_id: str = None
    title: str = None
    track_number: int = None

    def get_filename(self, suffix: str = "") -> str:
        """Returns a sane filename based on track number and title.

        If suffix is included, it will be appended to the filename.
        """
        return str(self.track_number).zfill(2) + "__" + text.get_filename(self.title) + suffix


# Combined Record Types (fields + other record types)
@dataclass
class Medium(Record):
    """A medium."""

    formats: ListF = None
    titles: list[str] = None
    track_count: int = None
    tracks: dict[int, Track] = None


@dataclass
class People(Record):
    """People."""

    arrangers: list[str] = None
    composers: list[str] = None
    conductors: list[str] = None
    engineers: list[str] = None
    lyricists: list[str] = None
    mixers: list[str] = None
    performers: (list[Performer], None) = None
    producers: list[str] = None
    writers: list[str] = None


@dataclass
class Release(Record):  # pylint: disable=too-many-instance-attributes
    """A release."""

    album: str = None
    album_artists: ListF = None
    album_artists_sort: ListF = None
    asins: list[str] = None
    barcodes: list[str] = None
    catalog_numbers: list[str] = None
    date: str = None
    front_cover: (FrontCover, None) = field(default=None, repr=False)
    genres: ListF = None
    labels: list[str] = None
    media: dict[int, Medium] = None
    medium_count: int = None
    musicbrainz_album_artist_ids: ListF = None
    musicbrainz_album_id: str = None
    musicbrainz_release_group_id: str = None
    original_date: str = None
    original_year: str = None
    people: People = None
    release_countries: list[str] = None
    release_statuses: list[str] = None
    release_types: list[str] = None
    script: str = None
    source: Source = None

    def get_artist_album_path(self) -> Path:
        """Returns a directory for the artist/album/disc combination.

        Example:
          -  artist__the/1969__the_album
        """
        artist_dir = Path(text.get_filename(self.album_artists_sort.first))
        album_dir = Path(text.get_filename(f"{self.original_year}__{self.album}"))
        return artist_dir / album_dir

    def pp(self, medium_number: int) -> str:  # pylint: disable=invalid-name
        """Returns a string summary of the Release."""
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


@dataclass
class OneTrack(Record):
    """A single track."""

    release: Release = None
    medium_number: int = None
    track_number: int = None

    @property
    def medium(self) -> (Medium, None):
        """The Medium object (or None)."""
        if self.release and self.release.media:
            return self.release.media[self.medium_number]
        return None

    @property
    def track(self) -> (Track, None):
        """The Track object (or None)."""
        if self.medium and self.medium.tracks:
            return self.medium.tracks[self.track_number]
        return None

    def get_artist_album_disc_path(self) -> Path:
        """Returns a directory for the artist/album/disc combination.

        Example:
          - artist__the/1969__the_album
          - artist__the/1969__the_album/disc2
        """
        if (self.medium_number, self.release.medium_count) == (1, 1):
            return self.release.get_artist_album_path()
        return self.release.get_artist_album_path() / f"disc{self.medium_number}"
