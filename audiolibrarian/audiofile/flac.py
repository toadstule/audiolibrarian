import re
from typing import List

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.audioinfo import (
    Info,
    Performer,
    RelationInfo,
    ReleaseInfo,
    TrackInfo,
)


class FlacFile(AudioFile):
    extensions = (".flac",)

    def read_tags(self) -> Info:
        print("> MUT_FILE:", self._mut_file)
        mut = self._mut_file
        release_info = ReleaseInfo(
            album=mut.get("album", [""])[0],
            album_artists=mut.get("albumartist", []),
            album_artists_sort=mut.get("albumartistsort", []),
            asins=mut.get("asin", []),
            barcodes=mut.get("barcode", []),
            catalog_numbers=mut.get("catalognumber", []),
            date=mut.get("date", [""])[0],
            disc_number=int(mut.get("discnumber", ["1"])[0]),
            disc_total=int(mut.get("disctotal", ["1"])[0]),
            genres=mut.get("genre", []),
            labels=mut.get("label", []),
            media=mut.get("media", []),
            musicbrainz_album_artist_ids=mut.get("musicbrainz_albumartistid", []),
            musicbrainz_album_id=mut.get("musicbrainz_albumid", [""])[0],
            musicbrainz_release_group_id=mut.get("musicbrainz_releasegroupid", [""])[0],
            original_date=mut.get("originaldate", [""])[0],
            original_year=int(mut.get("originalyear", ["0"])[0]),
            release_countries=mut.get("releasecountry", []),
            release_statuses=mut.get("releasestatus", []),
            release_types=mut.get("releasetype", []),
            script=mut.get("script", [""])[0],
            track_total=int(mut.get("tracktotal", ["0"])[0]),
        )
        track_info = TrackInfo(
            artist=mut.get("artist", [""])[0],
            artists=mut.get("artists", []),
            artists_sort=mut.get("artistsort", []),
            isrcs=mut.get("isrc", []),
            musicbrainz_artist_ids=mut.get("musicbrainz_artistid", []),
            musicbrainz_release_track_id=mut.get("musicbrainz_releasetrackid", [""])[0],
            musicbrainz_track_id=mut.get("musicbrainz_trackid", [""])[0],
            title=mut.get("title", [""])[0],
            track_number=mut.get("tracknumber", [""])[0],
        )
        relation_info = RelationInfo()
        if mut.get("engineer"):
            relation_info.engineers = mut["engineer"]
        if mut.get("lyricist"):
            relation_info.lyricists = mut["lyricist"]
        if mut.get("mixer"):
            relation_info.mixers = mut["mixer"]
        if mut.get("producer"):
            relation_info.producers = mut["producer"]
        if mut.get("performer"):
            relation_info.performers = self._parse_performer_tag(mut["performer"])
        return Info(relation_info=relation_info, release_info=release_info, track_info=track_info)

    def write_tags(self) -> None:
        relation_info = self._info.relation_info
        release_info = self._info.release_info
        track_info = self._info.track_info
        tags = {
            "album": [release_info.album],
            "albumartist": release_info.album_artists,
            "albumartistsort": release_info.album_artists_sort,
            "asin": release_info.asins,
            "barcode": release_info.barcodes,
            "catalognumber": release_info.catalog_numbers,
            "date": [release_info.date],
            "discnumber": [str(release_info.disc_number)],
            "disctotal": [str(release_info.disc_total)],
            "genre": release_info.genres,
            "label": release_info.labels,
            "media": release_info.media,
            "musicbrainz_albumartistid": release_info.musicbrainz_album_artist_ids,
            "musicbrainz_albumid": [release_info.musicbrainz_album_id],
            "musicbrainz_releasegroupid": [release_info.musicbrainz_release_group_id],
            "originaldate": [release_info.original_date],
            "originalyear": [str(release_info.original_year)],
            "releasecountry": release_info.release_countries,
            "releasestatus": release_info.release_statuses,
            "releasetype": release_info.release_types,
            "script": [release_info.script],
            "totaldiscs": [str(release_info.disc_total)],
            "tracktotal": [str(release_info.track_total)],
            "artist": [track_info.artist],
            "artists": track_info.artists,
            "artistsort": track_info.artists_sort,
            "isrc": track_info.isrcs,
            "musicbrainz_artistid": track_info.musicbrainz_artist_ids,
            "musicbrainz_releasetrackid": [track_info.musicbrainz_release_track_id],
            "musicbrainz_trackid": [track_info.musicbrainz_track_id],
            "title": [track_info.title],
            "tracknumber": [str(track_info.track_number)],
            "totaltracks": [str(release_info.track_total)],
        }
        if relation_info.engineers:
            tags["engineer"] = relation_info.engineers
        if relation_info.lyricists:
            tags["lyricist"] = relation_info.lyricists
        if relation_info.mixers:
            tags["mixer"] = relation_info.mixers
        if relation_info.producers:
            tags["producer"] = relation_info.producers
        if relation_info.performers:
            tags["performer"] = self._make_performer_tag(relation_info.performers)

        self._mut_file.delete()  # clear old tags
        self._mut_file.clear_pictures()
        self._mut_file.update(tags)

        # TO DO
        #     if info.front_cover:
        #         cover = mutagen.flac.Picture()
        #         cover.type = 3
        #         cover.mime = "image/jpeg"
        #         cover.desc = "front cover"
        #         cover.data = info.front_cover
        #         song.add_picture(cover)

        self._mut_file.save()

    @staticmethod
    def _make_performer_tag(performers: List[Performer]) -> List[str]:
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
