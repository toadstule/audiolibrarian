# Copyright (C) 2020 Stephen Jibson
#
# This file is part of AudioLibrarian.
#
# AudioLibrarian is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# AudioLibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Foobar.  If not, see
# <https://www.gnu.org/licenses/>.
#

from logging import getLogger
from typing import List

from mutagen.mp4 import AtomDataType, MP4Cover, MP4FreeForm

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.tags import Tags
from audiolibrarian.records import (
    BitrateMode,
    FileInfo,
    FileType,
    FrontCover,
    ListF,
    Medium,
    OneTrack,
    People,
    Release,
    Source,
    Track,
)

log = getLogger(__name__)
ITUNES = "----:com.apple.iTunes"


class M4aFile(AudioFile):
    """AudioFile for M4A files."""

    extensions = (".m4a",)

    def read_tags(self) -> OneTrack:
        """Reads the tags and returns a OneTrack object."""

        def get_str(key) -> (str, None):
            # Return first element for the given key, utf8-decoded.
            if mut.get(key) is None:
                return
            return mut.get(key)[0].decode("utf8")

        def get_strl(key) -> (ListF, None):
            # Return all elements for a given key, utf8-decoded.
            if mut.get(key) is None:
                return None
            return ListF([x.decode("utf8") for x in mut.get(key)])

        def listf(key) -> (ListF, None):
            # Return a ListF object for a given key.
            if mut.get(key) is None:
                return None
            return ListF(mut.get(key))

        mut = self._mut_file

        front_cover = None
        if mut.get("covr"):
            cover = mut["covr"][0]
            mime = "image/png" if cover.imageformat == AtomDataType.PNG else "image/jpg"
            front_cover = FrontCover(data=bytes(cover), mime=mime)
        medium_count = int(mut["disk"][0][1]) if mut.get("disk") else None
        medium_number = int(mut["disk"][0][0]) if mut.get("disk") else None
        track_count = int(mut["trkn"][0][1]) if mut.get("trkn") else None
        track_number = int(mut["trkn"][0][0]) if mut.get("trkn") else None
        release = (
            Release(
                album=mut.get("\xa9alb", [None])[0],
                album_artists=listf("aART"),
                album_artists_sort=listf("soaa"),
                asins=get_strl(f"{ITUNES}:ASIN"),
                barcodes=get_strl(f"{ITUNES}:BARCODE"),
                catalog_numbers=get_strl(f"{ITUNES}:CATALOGNUMBER"),
                date=mut.get("\xa9day", [None])[0],
                front_cover=front_cover,
                genres=listf("\xa9gen"),
                labels=get_strl(f"{ITUNES}:LABEL"),
                media={
                    medium_number: Medium(
                        formats=get_strl(f"{ITUNES}:MEDIA"),
                        titles=get_strl(f"{ITUNES}:DISCSUBTITLE"),
                        track_count=track_count,
                        tracks={
                            track_number: Track(
                                artist=mut.get("\xa9ART", [None])[0],
                                artists=get_strl(f"{ITUNES}:ARTISTS"),
                                artists_sort=mut.get("soar"),
                                file_info=FileInfo(
                                    bitrate=mut.info.bitrate // 1000,
                                    bitrate_mode=BitrateMode.CBR,
                                    path=self.filepath,
                                    type=FileType.AAC,
                                ),
                                isrcs=get_strl(f"{ITUNES}:ISRC"),
                                musicbrainz_artist_ids=get_strl(f"{ITUNES}:MusicBrainz Artist Id"),
                                musicbrainz_release_track_id=get_str(
                                    f"{ITUNES}:MusicBrainz Release Track Id"
                                ),
                                musicbrainz_track_id=get_str(f"{ITUNES}:MusicBrainz Track Id"),
                                title=mut.get("\xa9nam", [None])[0],
                                track_number=int(mut["trkn"][0][0]) if mut.get("trkn") else None,
                            )
                        }
                        if track_number
                        else None,
                    )
                }
                if medium_number
                else None,
                medium_count=medium_count,
                musicbrainz_album_artist_ids=get_strl(f"{ITUNES}:MusicBrainz Album Artist Id"),
                musicbrainz_album_id=get_str(f"{ITUNES}:MusicBrainz Album Id"),
                musicbrainz_release_group_id=get_str(f"{ITUNES}:MusicBrainz Release Group Id"),
                original_date=get_str(f"{ITUNES}:originaldate"),
                original_year=get_str(f"{ITUNES}:originalyear") or None,
                people=(
                    People(
                        arrangers=get_strl(f"{ITUNES}:ARRANGER"),
                        composers=get_strl(f"{ITUNES}:COMPOSER"),
                        conductors=get_strl(f"{ITUNES}:CONDUCTOR"),
                        engineers=get_strl(f"{ITUNES}:ENGINEER"),
                        lyricists=get_strl(f"{ITUNES}:LYRICIST"),
                        mixers=get_strl(f"{ITUNES}:MIXER"),
                        producers=get_strl(f"{ITUNES}:PRODUCER"),
                        performers=None,
                        writers=get_strl(f"{ITUNES}:WRITER"),
                    )
                    or None
                ),
                release_countries=get_strl(f"{ITUNES}:MusicBrainz Album Release Country"),
                release_statuses=get_strl(f"{ITUNES}:MusicBrainz Album Status"),
                release_types=get_strl(f"{ITUNES}:MusicBrainz Album Type"),
                script=get_str(f"{ITUNES}:SCRIPT"),
            )
            or None
        )
        if release:
            release.source = Source.TAGS
        return OneTrack(release=release, medium_number=medium_number, track_number=track_number)

    def write_tags(self) -> None:
        """Writes the tags."""

        def ff(s: (str, int, None)) -> (bytes, None):
            if s is None:
                return
            return MP4FreeForm(bytes(str(s), "utf8"))

        def ffl(list_: (List[str], None)) -> (ListF, None):
            if not list_:
                return
            return ListF([ff(x) for x in list_])

        # Note: We don't write "performers" to m4a files.
        release, medium_number, medium, track_number, track = self._get_tag_sources()
        front_cover = None
        if (c := release.front_cover) is not None:
            image_format = AtomDataType.PNG if c.mime == "image/png" else AtomDataType.JPEG
            front_cover = [MP4Cover(c.data, imageformat=image_format)]
        tags = {
            f"{ITUNES}:ARRANGER": ffl(release.people and release.people.arrangers),
            f"{ITUNES}:ARTISTS": ffl(track.artists),
            f"{ITUNES}:ASIN": ffl(release.asins),
            f"{ITUNES}:BARCODE": ffl(release.barcodes),
            f"{ITUNES}:CATALOGNUMBER": ffl(release.catalog_numbers),
            f"{ITUNES}:COMPOSER": ffl(release.people and release.people.composers),
            f"{ITUNES}:CONDUCTOR": ffl(release.people and release.people.conductors),
            f"{ITUNES}:DISCSUBTITLE": ffl(medium.titles),
            f"{ITUNES}:ENGINEER": ffl(release.people and release.people.engineers),
            f"{ITUNES}:ISRC": ffl(track.isrcs),
            f"{ITUNES}:LABEL": ffl(release.labels),
            f"{ITUNES}:LYRICIST": ffl(release.people and release.people.lyricists),
            f"{ITUNES}:MEDIA": ffl(medium.formats),
            f"{ITUNES}:MIXER": ffl(release.people and release.people.mixers),
            f"{ITUNES}:MusicBrainz Album Artist Id": ffl(release.musicbrainz_album_artist_ids),
            f"{ITUNES}:MusicBrainz Album Id": [ff(release.musicbrainz_album_id)],
            f"{ITUNES}:MusicBrainz Album Release Country": ffl(release.release_countries),
            f"{ITUNES}:MusicBrainz Album Status": ffl(release.release_statuses),
            f"{ITUNES}:MusicBrainz Album Type": ffl(release.release_types),
            f"{ITUNES}:MusicBrainz Artist Id": ffl(track.musicbrainz_artist_ids),
            f"{ITUNES}:MusicBrainz Release Group Id": [ff(release.musicbrainz_release_group_id)],
            f"{ITUNES}:MusicBrainz Release Track Id": [ff(track.musicbrainz_release_track_id)],
            f"{ITUNES}:MusicBrainz Track Id": [ff(track.musicbrainz_track_id)],
            f"{ITUNES}:originaldate": [ff(release.original_date)],
            f"{ITUNES}:originalyear": [ff(release.original_year)],
            f"{ITUNES}:PRODUCER": ffl(release.people and release.people.producers),
            f"{ITUNES}:SCRIPT": [ff(release.script)],
            f"{ITUNES}:WRITER": ffl(release.people and release.people.writers),
            "\xa9alb": [release.album],
            "\xa9ART": [track.artist],
            "\xa9day": [release.date],
            "\xa9gen": release.genres,
            "\xa9nam": [track.title],
            "aART": release.album_artists,
            "covr": front_cover,
            "disk": [(medium_number, release.medium_count)] if medium_number else None,
            "soaa": release.album_artists_sort,
            "soar": track.artists_sort,
            "trkn": [(track_number, medium.track_count)] if track_number else None,
        }
        tags = Tags(tags)

        for k, v in tags.items():
            try:
                self._mut_file[k] = v
            except Exception:
                log.critical("ERROR:", k, v)
                raise

        self._mut_file.save()
