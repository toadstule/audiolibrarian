import dataclasses
from dataclasses import dataclass
from typing import List


# Useful field reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py


@dataclass
class Record:
    def __bool__(self):
        return bool([x for x in dataclasses.asdict(self).values() if x is not None])


# Basic Record Types
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
    disc_number: int = None
    disc_total: int = None
    front_cover: (FrontCover, None) = None
    genres: List[str] = None
    labels: List[str] = None
    media: List[str] = None
    musicbrainz_album_artist_ids: List[str] = None
    musicbrainz_album_id: str = None
    musicbrainz_release_group_id: str = None
    original_date: str = None
    original_year: int = None
    people: People = None
    release_countries: List[str] = None
    release_statuses: List[str] = None
    release_types: List[str] = None
    script: str = None
    track_total: int = None


# View Record Types (no fields)
@dataclass
class ReleaseView(Record):
    people: People
    release: Release
    tracks: List[Track]


@dataclass
class TrackView(Record):
    release: Release
    track: Track
