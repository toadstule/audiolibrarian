from dataclasses import dataclass
from typing import List


# Useful reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py


@dataclass
class FrontCover:
    data: bytes = None
    desc: str = None
    mime: str = None


@dataclass
class ReleaseInfo:
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
    release_countries: List[str] = None
    release_statuses: List[str] = None
    release_types: List[str] = None
    script: str = None
    track_total: int = None


@dataclass
class Performer:
    name: str = None
    instrument: str = None


@dataclass
class RelationInfo:
    engineers: List[str] = None
    lyricists: List[str] = None
    mixers: List[str] = None
    performers: (List[Performer], None) = None
    producers: List[str] = None


@dataclass
class TrackInfo:
    artist: str = None
    artists: List[str] = None
    artists_sort: List[str] = None
    isrcs: List[str] = None
    musicbrainz_artist_ids: List[str] = None
    musicbrainz_release_track_id: str = None
    musicbrainz_track_id: str = None
    title: str = None
    track_number: int = None


@dataclass
class Info:
    relation_info: (RelationInfo, None)
    release_info: (ReleaseInfo, None)
    track_info: (TrackInfo, None)
