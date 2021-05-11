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
import enum
import pathlib
from typing import Any, Optional

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


class ListF(list):
    """A list, with a first property."""

    @property
    def first(self) -> Optional[Any]:
        """Return the first element in the list (or None, if the list is empty)."""
        if self:
            return self[0]
        return None


@dataclasses.dataclass
class Record:
    """Base class for records.

    Overrides true/false test for records returning false if all fields are None.
    """

    def __bool__(self):
        """Return a boolean representation of the Record."""
        return bool([x for x in dataclasses.asdict(self).values() if x is not None])

    def asdict(self) -> dict:
        """Return a dict version of the record."""
        return dataclasses.asdict(self)


# Primitive Record Types
@dataclasses.dataclass
class FileInfo(Record):
    """File information."""

    bitrate: Optional[int] = None
    bitrate_mode: Optional[BitrateMode] = None
    path: Optional[pathlib.Path] = None
    type: Optional[FileType] = None


@dataclasses.dataclass
class FrontCover(Record):
    """A front cover."""

    data: Optional[bytes] = None
    desc: Optional[str] = None
    mime: Optional[str] = None


@dataclasses.dataclass
class Performer(Record):
    """A performer with an instrument."""

    name: Optional[str] = None
    instrument: Optional[str] = None


@dataclasses.dataclass
class Track(Record):
    """A track."""

    artist: Optional[str] = None
    artists: Optional[ListF] = None
    artists_sort: Optional[list[str]] = None
    file_info: Optional[FileInfo] = None
    isrcs: Optional[list[str]] = None
    musicbrainz_artist_ids: Optional[ListF] = None
    musicbrainz_release_track_id: Optional[str] = None
    musicbrainz_track_id: Optional[str] = None
    title: Optional[str] = None
    track_number: Optional[int] = None

    def get_filename(self, suffix: str = "") -> str:
        """Return a sane filename based on track number and title.

        If suffix is included, it will be appended to the filename.
        """
        return str(self.track_number).zfill(2) + "__" + text.get_filename(self.title) + suffix


# Combined Record Types (fields + other record types)
@dataclasses.dataclass
class Medium(Record):
    """A medium."""

    formats: Optional[ListF] = None
    titles: Optional[list[str]] = None
    track_count: Optional[int] = None
    tracks: Optional[dict[int, Track]] = None


@dataclasses.dataclass
class People(Record):
    """People."""

    arrangers: Optional[list[str]] = None
    composers: Optional[list[str]] = None
    conductors: Optional[list[str]] = None
    engineers: Optional[list[str]] = None
    lyricists: Optional[list[str]] = None
    mixers: Optional[list[str]] = None
    performers: Optional[list[Performer]] = None
    producers: Optional[list[str]] = None
    writers: Optional[list[str]] = None


@dataclasses.dataclass
class Release(Record):  # pylint: disable=too-many-instance-attributes
    """A release."""

    album: Optional[str] = None
    album_artists: Optional[ListF] = None
    album_artists_sort: Optional[ListF] = None
    asins: Optional[list[str]] = None
    barcodes: Optional[list[str]] = None
    catalog_numbers: Optional[list[str]] = None
    date: Optional[str] = None
    front_cover: Optional[FrontCover] = dataclasses.field(default=None, repr=False)
    genres: Optional[ListF] = None
    labels: Optional[list[str]] = None
    media: Optional[dict[int, Medium]] = None
    medium_count: Optional[int] = None
    musicbrainz_album_artist_ids: Optional[ListF] = None
    musicbrainz_album_id: Optional[str] = None
    musicbrainz_release_group_id: Optional[str] = None
    original_date: Optional[str] = None
    original_year: Optional[str] = None
    people: Optional[People] = None
    release_countries: Optional[list[str]] = None
    release_statuses: Optional[list[str]] = None
    release_types: Optional[list[str]] = None
    script: Optional[str] = None
    source: Optional[Source] = None

    def get_artist_album_path(self) -> pathlib.Path:
        """Return a directory for the artist/album/disc combination.

        Example:
          -  artist__the/1969__the_album
        """
        artist_dir = pathlib.Path(text.get_filename(self.album_artists_sort.first))
        album_dir = pathlib.Path(text.get_filename(f"{self.original_year}__{self.album}"))
        return artist_dir / album_dir

    def pp(self, medium_number: int) -> str:  # pylint: disable=invalid-name
        """Return a string summary of the Release."""
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


@dataclasses.dataclass
class OneTrack(Record):
    """A single track."""

    release: Optional[Release] = None
    medium_number: Optional[int] = None
    track_number: Optional[int] = None

    @property
    def medium(self) -> Optional[Medium]:
        """Return the Medium object (or None)."""
        if self.release and self.release.media:
            return self.release.media[self.medium_number]
        return None

    @property
    def track(self) -> Optional[Track]:
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
