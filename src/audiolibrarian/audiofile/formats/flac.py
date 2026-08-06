#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""AudioFile support for flac files."""

import re
from typing import Any

import attrs
import mutagen.flac

from audiolibrarian import audiofile
from audiolibrarian.domain.model import enums, release, values
from audiolibrarian.domain.model.medium import Medium
from audiolibrarian.domain.model.record import ListF
from audiolibrarian.domain.model.release import Release
from audiolibrarian.domain.model.track import Track


class FlacFile(audiofile.AudioFile, extensions={".flac"}):
    """AudioFile for Flac files."""

    def read_tags(self) -> release.OneTrack:
        """Read the tags and return a OneTrack object."""

        def listf[T](lst: list[T] | None) -> ListF[T] | None:
            if lst is None:
                return None
            return ListF(lst)

        mut = self._mut_file
        front_cover = None
        if self._mut_file.pictures:
            cover = self._mut_file.pictures[0]
            front_cover = values.FrontCover(data=cover.data, desc=cover.desc or "", mime=cover.mime)
        medium_count = int(mut["disctotal"][0]) if mut.get("disctotal") else None
        medium_number = int(mut["discnumber"][0]) if mut.get("discnumber") else None
        track_count = int(mut["tracktotal"][0]) if mut.get("tracktotal") else None
        track_number = values.TrackNumber(int(mut["tracknumber"][0])) if mut.get("tracknumber") else None

        # Create MediumPosition if we have both number and count
        medium_position = None
        if medium_number is not None and medium_count is not None:
            medium_position = values.MediumPosition(number=medium_number, count=medium_count)

        release_obj = (
            Release(
                album=mut.get("album", [None])[0],
                album_artists=listf(mut.get("albumartist")),
                album_artists_sort=listf(mut.get("albumartistsort")),
                asins=mut.get("asin"),
                barcodes=mut.get("barcode"),
                catalog_numbers=mut.get("catalognumber"),
                date=mut.get("date", [None])[0],
                front_cover=front_cover,
                genres=listf(mut.get("genre")),
                labels=mut.get("label"),
                media={
                    medium_number: Medium(
                        formats=listf(mut.get("media")),
                        titles=mut.get("discsubtitle"),
                        track_count=track_count,
                        tracks={
                            track_number: Track(
                                artist=mut.get("artist", [None])[0],
                                artists=listf(mut.get("artists")),
                                artists_sort=mut.get("artistsort"),
                                file_info=values.FileInfo(
                                    bitrate=mut.info.bitrate // 1000,
                                    bitrate_mode=enums.BitrateMode.CBR,
                                    path=self.filepath,
                                    type=enums.FileFormat.FLAC,
                                ),
                                isrcs=mut.get("isrc"),
                                musicbrainz_artist_ids=listf(mut.get("musicbrainz_artistid")),
                                musicbrainz_release_track_id=mut.get("musicbrainz_releasetrackid", [None])[0],
                                musicbrainz_track_id=mut.get("musicbrainz_trackid", [None])[0],
                                title=mut.get("title", [None])[0],
                                track_number=track_number,
                            )
                        }
                        if track_number
                        else None,
                    )
                }
                if medium_number
                else None,
                medium_count=medium_count,
                musicbrainz_album_artist_ids=listf(mut.get("musicbrainz_albumartistid")),
                musicbrainz_album_id=mut.get("musicbrainz_albumid", [None])[0],
                musicbrainz_release_group_id=mut.get("musicbrainz_releasegroupid", [None])[0],
                original_date=mut.get("originaldate", [None])[0],
                original_year=mut["originalyear"][0] if mut.get("originalyear") else None,
                people=(
                    values.People(
                        arrangers=mut.get("arranger"),
                        composers=mut.get("composer"),
                        conductors=mut.get("conductor"),
                        engineers=mut.get("engineer"),
                        lyricists=mut.get("lyricist"),
                        mixers=mut.get("mixer"),
                        performers=mut.get("performer") and self._parse_performer_tag(mut["performer"]),
                        producers=mut.get("producer"),
                        writers=mut.get("writer"),
                    )
                    or None
                ),
                release_countries=mut.get("releasecountry"),
                release_statuses=mut.get("releasestatus"),
                release_types=mut.get("releasetype"),
                script=mut.get("script", [None])[0],
            )
            or None
        )
        if release_obj:
            release_obj = attrs.evolve(release_obj, source=enums.Source.TAGS)
        return release.OneTrack(release=release_obj, medium_position=medium_position, track_number=track_number)

    def write_tags(self) -> None:
        """Write the tags."""
        release_, medium_number, medium, track_number, track = self._get_tag_sources()
        tags_ = {
            "album": [release_.album],
            "albumartist": release_.album_artists,
            "albumartistsort": release_.album_artists_sort,
            "arranger": release_.people and release_.people.arrangers,
            "artist": [track.artist],
            "artists": track.artists,
            "artistsort": track.artists_sort,
            "asin": release_.asins,
            "barcode": release_.barcodes,
            "catalognumber": release_.catalog_numbers,
            "composer": release_.people and release_.people.composers,
            "conductor": release_.people and release_.people.conductors,
            "date": [release_.date],
            "discnumber": [str(medium_number)],
            "discsubtitle": medium.titles,
            "disctotal": [str(release_.medium_count)],
            "engineer": release_.people and release_.people.engineers,
            "genre": release_.genres,
            "isrc": track.isrcs,
            "label": release_.labels,
            "lyricist": release_.people and release_.people.lyricists,
            "media": medium.formats,
            "mixer": release_.people and release_.people.mixers,
            "musicbrainz_albumartistid": release_.musicbrainz_album_artist_ids,
            "musicbrainz_albumid": [release_.musicbrainz_album_id],
            "musicbrainz_artistid": track.musicbrainz_artist_ids,
            "musicbrainz_releasegroupid": [release_.musicbrainz_release_group_id],
            "musicbrainz_releasetrackid": [track.musicbrainz_release_track_id],
            "musicbrainz_trackid": [track.musicbrainz_track_id],
            "originaldate": [release_.original_date],
            "originalyear": [str(release_.original_year)],
            "performer": self._make_performer_tag(release_.people and release_.people.performers),
            "producer": release_.people and release_.people.producers,
            "releasecountry": release_.release_countries,
            "releasestatus": release_.release_statuses,
            "releasetype": release_.release_types,
            "script": [release_.script],
            "title": [track.title],
            "totaldiscs": [str(release_.medium_count)],
            "totaltracks": [str(medium.track_count)],
            "tracknumber": [str(track_number.value if track_number else None)],
            "tracktotal": [str(medium.track_count)],
            "writer": release_.people and release_.people.writers,
        }
        tags_ = audiofile.Tags(tags_)
        self._mut_file.delete()  # Clear old tags.
        self._mut_file.clear_pictures()
        self._mut_file.update(tags_)

        if release_.front_cover is not None:
            cover = mutagen.flac.Picture()  # type: ignore[no-untyped-call]
            cover.type = 3
            cover.mime = release_.front_cover.mime
            cover.desc = release_.front_cover.desc or ""
            cover.data = release_.front_cover.data
            self._mut_file.add_picture(cover)

        self._mut_file.save()

    @staticmethod
    def _make_performer_tag(performers: list[values.Performer] | Any | None) -> list[str] | None:  # noqa: ANN401
        # Return a list of performer tag strings "name (instrument)".
        if performers is None:
            return None
        return [f"{p.name} ({p.instrument})" for p in performers]

    @staticmethod
    def _parse_performer_tag(performers_tag: list[str]) -> list[values.Performer]:
        # Parse a list of performer tags and return a list of Performer objects.
        performer_re = re.compile(r"(?P<name>.*)\((?P<instrument>.*)\)")
        performers = []
        for tag in performers_tag:
            if match := performer_re.match(tag):
                name = match.groupdict()["name"].strip()
                instrument = match.groupdict()["instrument"].strip()
                performers.append(values.Performer(name=name, instrument=instrument))
        return performers
