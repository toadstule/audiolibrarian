import re
from typing import List

import mutagen.flac

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.tags import Tags
from audiolibrarian.records import (
    FrontCover,
    People,
    Performer,
    Release,
    Track,
    TrackView,
)


class FlacFile(AudioFile):
    extensions = (".flac",)

    def read_tags(self) -> TrackView:
        mut = self._mut_file

        front_cover = None
        if self._mut_file.pictures:
            cover = self._mut_file.pictures[0]
            front_cover = FrontCover(data=cover.data, desc=cover.desc or "", mime=cover.mime)

        release = Release(
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
            original_year=mut["originalyear"][0] if mut.get("originalyear") else None,
            people=(
                People(
                    engineers=mut.get("engineer"),
                    lyricists=mut.get("lyricist"),
                    mixers=mut.get("mixer"),
                    performers=mut.get("performer")
                    and self._parse_performer_tag(mut["performer"]),
                    producers=mut.get("producer"),
                )
                or None
            ),
            release_countries=mut.get("releasecountry"),
            release_statuses=mut.get("releasestatus"),
            release_types=mut.get("releasetype"),
            script=mut.get("script", [None])[0],
            track_total=int(mut["tracktotal"][0]) if mut.get("tracktotal") else None,
        )
        track = Track(
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
        return TrackView(release=release, track=track)

    def write_tags(self) -> None:

        release = self._track_view.release
        track = self._track_view.track
        tags = {
            "album": [release.album],
            "albumartist": release.album_artists,
            "albumartistsort": release.album_artists_sort,
            "artist": [track.artist],
            "artists": track.artists,
            "artistsort": track.artists_sort,
            "asin": release.asins,
            "barcode": release.barcodes,
            "catalognumber": release.catalog_numbers,
            "date": [release.date],
            "discnumber": [str(release.disc_number)],
            "disctotal": [str(release.disc_total)],
            "engineer": release.people and release.people.engineers,
            "genre": release.genres,
            "isrc": track.isrcs,
            "label": release.labels,
            "lyricist": release.people and release.people.lyricists,
            "media": release.media,
            "mixer": release.people and release.people.mixers,
            "musicbrainz_albumartistid": release.musicbrainz_album_artist_ids,
            "musicbrainz_albumid": [release.musicbrainz_album_id],
            "musicbrainz_artistid": track.musicbrainz_artist_ids,
            "musicbrainz_releasegroupid": [release.musicbrainz_release_group_id],
            "musicbrainz_releasetrackid": [track.musicbrainz_release_track_id],
            "musicbrainz_trackid": [track.musicbrainz_track_id],
            "originaldate": [release.original_date],
            "originalyear": [str(release.original_year)],
            "performer": self._make_performer_tag(release.people and release.people.performers),
            "producer": release.people and release.people.producers,
            "releasecountry": release.release_countries,
            "releasestatus": release.release_statuses,
            "releasetype": release.release_types,
            "script": [release.script],
            "title": [track.title],
            "totaldiscs": [str(release.disc_total)],
            "totaltracks": [str(release.track_total)],
            "tracknumber": [str(track.track_number)],
            "tracktotal": [str(release.track_total)],
        }
        tags = Tags(tags)
        self._mut_file.delete()  # clear old tags
        self._mut_file.clear_pictures()
        self._mut_file.update(tags)

        if release.front_cover is not None:
            cover = mutagen.flac.Picture()
            cover.type = 3
            cover.mime = release.front_cover.mime
            cover.desc = release.front_cover.desc or ""
            cover.data = release.front_cover.data
            self._mut_file.add_picture(cover)

        self._mut_file.save()

    @staticmethod
    def _make_performer_tag(performers: List[Performer]) -> List[str]:
        if performers:
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
