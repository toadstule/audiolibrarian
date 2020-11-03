import re
from typing import List

import mutagen.flac

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audioinfo2 import (
    FrontCover,
    Info,
    Performer,
    RelationInfo,
    ReleaseInfo,
    TrackInfo,
)
from audiolibrarian.audiofile.tags import Tags


class FlacFile(AudioFile):
    extensions = (".flac",)

    def read_tags(self) -> Info:
        mut = self._mut_file

        front_cover = None
        if self._mut_file.pictures:
            cover = self._mut_file.pictures[0]
            front_cover = FrontCover(data=cover.data, desc=cover.desc or "", mime=cover.mime)

        release_info = ReleaseInfo(
            album=mut.get("album", [None])[0],
            album_artists=mut.get("albumartist"),
            album_artists_sort=mut.get("albumartistsort"),
            asins=mut.get("asin"),
            barcodes=mut.get("barcode"),
            catalog_numbers=mut.get("catalognumber"),
            date=mut.get("date", [None])[0],
            disc_number=int(mut["discnumber"][0]) if mut.get("discnumber") else None,
            disc_total=int(mut["disctotal"][0]) if mut.get("disctotal") else None,
            front_cover=front_cover,
            genres=mut.get("genre"),
            labels=mut.get("label"),
            media=mut.get("media"),
            musicbrainz_album_artist_ids=mut.get("musicbrainz_albumartistid"),
            musicbrainz_album_id=mut.get("musicbrainz_albumid", [None])[0],
            musicbrainz_release_group_id=mut.get("musicbrainz_releasegroupid", [None])[0],
            original_date=mut.get("originaldate", [None])[0],
            original_year=int(mut["originalyear"][0]) if mut.get("originalyear") else None,
            release_countries=mut.get("releasecountry"),
            release_statuses=mut.get("releasestatus"),
            release_types=mut.get("releasetype"),
            script=mut.get("script", [None])[0],
            track_total=int(mut["tracktotal"][0]) if mut.get("tracktotal") else None,
        )
        track_info = TrackInfo(
            artist=mut.get("artist", [None])[0],
            artists=mut.get("artists"),
            artists_sort=mut.get("artistsort"),
            isrcs=mut.get("isrc"),
            musicbrainz_artist_ids=mut.get("musicbrainz_artistid"),
            musicbrainz_release_track_id=mut.get("musicbrainz_releasetrackid", [None])[0],
            musicbrainz_track_id=mut.get("musicbrainz_trackid", [None])[0],
            title=mut.get("title", [None])[0],
            track_number=int(mut["tracknumber"][0]) if mut.get("tracknumber") else None,
        )
        relation_info = RelationInfo(
            engineers=mut.get("engineer"),
            lyricists=mut.get("lyricist"),
            mixers=mut.get("mixer"),
            performers=mut.get("performer") and self._parse_performer_tag(mut["performer"]),
            producers=mut.get("producer"),
        )

        return Info(relation_info=relation_info, release_info=release_info, track_info=track_info)

    def write_tags(self) -> None:

        relation_info = self._info.relation_info
        release_info = self._info.release_info
        track_info = self._info.track_info
        tags = {
            "album": [release_info.album],
            "albumartist": release_info.album_artists,
            "albumartistsort": release_info.album_artists_sort,
            "artist": [track_info.artist],
            "artists": track_info.artists,
            "artistsort": track_info.artists_sort,
            "asin": release_info.asins,
            "barcode": release_info.barcodes,
            "catalognumber": release_info.catalog_numbers,
            "date": [release_info.date],
            "discnumber": [str(release_info.disc_number)],
            "disctotal": [str(release_info.disc_total)],
            "engineer": relation_info.engineers,
            "genre": release_info.genres,
            "isrc": track_info.isrcs,
            "label": release_info.labels,
            "lyricist": relation_info.lyricists,
            "media": release_info.media,
            "mixer": relation_info.mixers,
            "musicbrainz_albumartistid": release_info.musicbrainz_album_artist_ids,
            "musicbrainz_albumid": [release_info.musicbrainz_album_id],
            "musicbrainz_artistid": track_info.musicbrainz_artist_ids,
            "musicbrainz_releasegroupid": [release_info.musicbrainz_release_group_id],
            "musicbrainz_releasetrackid": [track_info.musicbrainz_release_track_id],
            "musicbrainz_trackid": [track_info.musicbrainz_track_id],
            "originaldate": [release_info.original_date],
            "originalyear": [str(release_info.original_year)],
            "performer": self._make_performer_tag(relation_info.performers),
            "producer": relation_info.producers,
            "releasecountry": release_info.release_countries,
            "releasestatus": release_info.release_statuses,
            "releasetype": release_info.release_types,
            "script": [release_info.script],
            "title": [track_info.title],
            "totaldiscs": [str(release_info.disc_total)],
            "totaltracks": [str(release_info.track_total)],
            "tracknumber": [str(track_info.track_number)],
            "tracktotal": [str(release_info.track_total)],
        }
        tags = Tags(tags)
        self._mut_file.delete()  # clear old tags
        self._mut_file.clear_pictures()
        self._mut_file.update(tags)

        if release_info.front_cover is not None:
            cover = mutagen.flac.Picture()
            cover.type = 3
            cover.mime = release_info.front_cover.mime
            cover.desc = release_info.front_cover.desc or ""
            cover.data = release_info.front_cover.data
            self._mut_file.add_picture(cover)

        self._mut_file.save()

    @staticmethod
    def _make_performer_tag(performers: List[Performer]) -> List[str]:
        if performers is not None:
            return [f"{p.name} ({p.instrument})" for p in performers]

    @staticmethod
    def _parse_performer_tag(performers_tag: List[str]) -> List[Performer]:
        performer_re = re.compile(r"(?P<name>.*)\((?P<instrument>.*)\)")
        performers = []
        for p in performers_tag:
            if match := performer_re.match(p):
                name = match.groupdict()["name"].strip()
                instrument = match.groupdict()["instrument"].strip()
                performers.append(Performer(name=name, instrument=instrument))
        return performers
