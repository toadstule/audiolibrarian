# Copyright (C) 2020 Stephen Jibson

"""Record (dataclass) definitions."""

# Useful field reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py

import dataclasses
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List

from audiolibrarian import text


class BitrateMode(Enum):
    UNKNOWN = 0
    CBR = 1
    VBR = 2


class FileType(Enum):
    UNKNOWN = 0
    AAC = 1
    FLAC = 2
    MP3 = 3
    WAV = 4


class Source(Enum):
    MUSICBRAINZ = 1
    TAGS = 2


@dataclass
class Record:
    """Base class for records.

    Overrides true/false test for records returning false if all fields are None."""

    def __bool__(self):
        return bool([x for x in asdict(self).values() if x is not None])

    def asdict(self) -> Dict:
        """Returns a dict version of the record."""
        return dataclasses.asdict(self)

    def first(self, name):
        """Returns the first element of a list-type field."""
        try:
            return getattr(self, name)[0]
        except (TypeError, AttributeError):
            return


# Primitive Record Types
@dataclass
class FileInfo(Record):
    bitrate: int = None
    bitrate_mode: BitrateMode = None
    path: Path = None
    type: FileType = None


@dataclass
class FrontCover(Record):
    data: bytes = None
    desc: str = None
    mime: str = None


@dataclass
class Performer(Record):
    name: str = None
    instrument: str = None


@dataclass
class Track(Record):
    artist: str = None
    artists: List[str] = None
    artists_sort: List[str] = None
    file_info: FileInfo = None
    isrcs: List[str] = None
    musicbrainz_artist_ids: List[str] = None
    musicbrainz_release_track_id: str = None
    musicbrainz_track_id: str = None
    title: str = None
    track_number: int = None

    def get_filename(self) -> str:
        """Returns a sane filename based on track number and title."""
        return str(self.track_number).zfill(2) + "__" + text.get_filename(self.title)


# Combined Record Types (fields + other record types)
@dataclass
class Medium(Record):
    formats: List[str] = None
    titles: List[str] = None
    track_count: int = None
    tracks: Dict[int, Track] = None


@dataclass
class People(Record):
    engineers: List[str] = None
    lyricists: List[str] = None
    mixers: List[str] = None
    performers: (List[Performer], None) = None
    producers: List[str] = None


@dataclass
class Release(Record):
    album: str = None
    album_artists: List[str] = None
    album_artists_sort: List[str] = None
    asins: List[str] = None
    barcodes: List[str] = None
    catalog_numbers: List[str] = None
    date: str = None
    front_cover: (FrontCover, None) = field(default=None, repr=False)
    genres: List[str] = None
    labels: List[str] = None
    media: Dict[int, Medium] = None
    medium_count: int = None
    musicbrainz_album_artist_ids: List[str] = None
    musicbrainz_album_id: str = None
    musicbrainz_release_group_id: str = None
    original_date: str = None
    original_year: str = None
    people: People = None
    release_countries: List[str] = None
    release_statuses: List[str] = None
    release_types: List[str] = None
    script: str = None
    source: Source = None

    def pp(self, medium_number: int) -> str:
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
    release: Release = None
    medium_number: int = None
    track_number: int = None

    @property
    def medium(self) -> (Medium, None):
        """The Medium object (or None)."""
        if self.release and self.release.media:
            return self.release.media[self.medium_number]

    @property
    def track(self) -> (Track, None):
        """The Track object (or None)."""
        if self.medium and self.medium.tracks:
            return self.medium.tracks[self.track_number]
