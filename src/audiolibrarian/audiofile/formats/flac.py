"""AudioFile support for flac files."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
import re
from typing import Any

import mutagen.flac

from audiolibrarian import audiofile, records


class FlacFile(audiofile.AudioFile, extensions={".flac"}):
    """AudioFile for Flac files."""

    def read_tags(self) -> records.OneTrack:
        """Read the tags and return a OneTrack object."""

        def listf(lst: list[Any] | None) -> records.ListF | None:
            if lst is None:
                return None
            return records.ListF(lst)

        mut = self._mut_file
        front_cover = None
        if self._mut_file.pictures:
            cover = self._mut_file.pictures[0]
            front_cover = records.FrontCover(
                data=cover.data, desc=cover.desc or "", mime=cover.mime
            )
        medium_count = int(mut["disctotal"][0]) if mut.get("disctotal") else None
        medium_number = int(mut["discnumber"][0]) if mut.get("discnumber") else None
        track_count = int(mut["tracktotal"][0]) if mut.get("tracktotal") else None
        track_number = int(mut["tracknumber"][0]) if mut.get("tracknumber") else None
        release = (
            records.Release(
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
                    medium_number: records.Medium(
                        formats=listf(mut.get("media")),
                        titles=mut.get("discsubtitle"),
                        track_count=track_count,
                        tracks={
                            track_number: records.Track(
                                artist=mut.get("artist", [None])[0],
                                artists=listf(mut.get("artists")),
                                artists_sort=mut.get("artistsort"),
                                file_info=records.FileInfo(
                                    bitrate=mut.info.bitrate // 1000,
                                    bitrate_mode=records.BitrateMode.CBR,
                                    path=self.filepath,
                                    type=records.FileType.FLAC,
                                ),
                                isrcs=mut.get("isrc"),
                                musicbrainz_artist_ids=listf(mut.get("musicbrainz_artistid")),
                                musicbrainz_release_track_id=mut.get(
                                    "musicbrainz_releasetrackid", [None]
                                )[0],
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
                    records.People(
                        arrangers=mut.get("arranger"),
                        composers=mut.get("composer"),
                        conductors=mut.get("conductor"),
                        engineers=mut.get("engineer"),
                        lyricists=mut.get("lyricist"),
                        mixers=mut.get("mixer"),
                        performers=mut.get("performer")
                        and self._parse_performer_tag(mut["performer"]),
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
        if release:
            release.source = records.Source.TAGS
        return records.OneTrack(
            release=release, medium_number=medium_number, track_number=track_number
        )

    def write_tags(self) -> None:
        """Write the tags."""
        release, medium_number, medium, track_number, track = self._get_tag_sources()
        tags_ = {
            "album": [release.album],
            "albumartist": release.album_artists,
            "albumartistsort": release.album_artists_sort,
            "arranger": release.people and release.people.arrangers,
            "artist": [track.artist],
            "artists": track.artists,
            "artistsort": track.artists_sort,
            "asin": release.asins,
            "barcode": release.barcodes,
            "catalognumber": release.catalog_numbers,
            "composer": release.people and release.people.composers,
            "conductor": release.people and release.people.conductors,
            "date": [release.date],
            "discnumber": [str(medium_number)],
            "discsubtitle": medium.titles,
            "disctotal": [str(release.medium_count)],
            "engineer": release.people and release.people.engineers,
            "genre": release.genres,
            "isrc": track.isrcs,
            "label": release.labels,
            "lyricist": release.people and release.people.lyricists,
            "media": medium.formats,
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
            "totaldiscs": [str(release.medium_count)],
            "totaltracks": [str(medium.track_count)],
            "tracknumber": [str(track_number)],
            "tracktotal": [str(medium.track_count)],
            "writer": release.people and release.people.writers,
        }
        tags_ = audiofile.Tags(tags_)
        self._mut_file.delete()  # Clear old tags.
        self._mut_file.clear_pictures()
        self._mut_file.update(tags_)

        if release.front_cover is not None:
            cover = mutagen.flac.Picture()  # type: ignore[no-untyped-call]
            cover.type = 3
            cover.mime = release.front_cover.mime
            cover.desc = release.front_cover.desc or ""
            cover.data = release.front_cover.data
            self._mut_file.add_picture(cover)

        self._mut_file.save()

    @staticmethod
    def _make_performer_tag(performers: list[records.Performer] | None | Any) -> list[str] | None:  # noqa: ANN401
        # Return a list of performer tag strings "name (instrument)".
        if performers is None:
            return None
        return [f"{p.name} ({p.instrument})" for p in performers]

    @staticmethod
    def _parse_performer_tag(performers_tag: list[str]) -> list[records.Performer]:
        # Parse a list of performer tags and return a list of Performer objects.
        performer_re = re.compile(r"(?P<name>.*)\((?P<instrument>.*)\)")
        performers = []
        for tag in performers_tag:
            if match := performer_re.match(tag):
                name = match.groupdict()["name"].strip()
                instrument = match.groupdict()["instrument"].strip()
                performers.append(records.Performer(name=name, instrument=instrument))
        return performers
