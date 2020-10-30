from dataclasses import dataclass, field
from typing import List

# Useful reference: https://github.com/metabrainz/picard/blob/master/picard/util/tags.py


@dataclass
class ReleaseInfo:
    album: str = ""
    album_artists: List[str] = field(default_factory=list)
    album_artists_sort: List[str] = field(default_factory=list)
    asins: List[str] = field(default_factory=list)
    barcodes: List[str] = field(default_factory=list)
    catalog_numbers: List[str] = field(default_factory=list)
    date: str = ""
    description: str = ""
    disc_number: int = 1
    disc_total: int = 1
    genres: List[str] = field(default_factory=list)
    labels: List[str] = field(default_factory=list)
    media: List[str] = field(default_factory=list)
    musicbrainz_album_artist_ids: List[str] = field(default_factory=list)
    musicbrainz_album_id: str = ""
    musicbrainz_release_group_id: str = ""
    original_date: str = ""
    original_year: int = 0
    release_countries: List[str] = field(default_factory=list)
    release_statuses: List[str] = field(default_factory=list)
    release_types: List[str] = field(default_factory=list)
    script: str = ""
    track_total: int = 1


@dataclass
class Performer:
    name: str = ""
    instrument: str = ""


@dataclass
class RelationInfo:
    engineers: List[str] = field(default_factory=list)
    lyricists: List[str] = field(default_factory=list)
    mixers: List[str] = field(default_factory=list)
    performers: List[Performer] = field(default_factory=list)
    producers: List[str] = field(default_factory=list)


@dataclass
class TrackInfo:
    artist: str = ""
    artists: List[str] = field(default_factory=list)
    artists_sort: List[str] = field(default_factory=list)
    isrcs: List[str] = field(default_factory=list)
    musicbrainz_artist_ids: List[str] = field(default_factory=list)
    musicbrainz_release_track_id: str = ""
    musicbrainz_track_id: str = ""
    title: str = ""
    track_number: int = 0


@dataclass
class Info:
    relation_info: (RelationInfo, None)
    release_info: (ReleaseInfo, None)
    track_info: (TrackInfo, None)
