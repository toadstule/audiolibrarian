import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List


# Useful field reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py


class Source(Enum):
    MUSICBRAINZ = 1
    TAGS = 2


@dataclass
class Record:
    def __bool__(self):
        return bool([x for x in dataclasses.asdict(self).values() if x is not None])


# Primitive Record Types
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
    isrcs: List[str] = None
    musicbrainz_artist_ids: List[str] = None
    musicbrainz_release_track_id: str = None
    musicbrainz_track_id: str = None
    title: str = None
    track_number: int = None


# Combined Record Types (fields + other record types)
@dataclass
class Medium(Record):
    format: List[str] = None
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
    front_cover: (FrontCover, None) = None
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


@dataclass
class OneTrack(Record):
    release: Release = None
    medium_number: int = None
    track_number: int = None

    @property
    def medium(self):
        if self.release and self.release.media:
            return self.release.media[self.medium_number]

    @property
    def track(self):
        if self.medium and self.medium.tracks:
            return self.medium.tracks[self.track_number]
