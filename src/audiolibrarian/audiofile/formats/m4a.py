"""AudioFile support for m4a files."""

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
from logging import getLogger
from typing import Any

import attrs
import mutagen.mp4

from audiolibrarian import audiofile
from audiolibrarian.domain.model import enums, record, release, values
from audiolibrarian.domain.model.medium import Medium
from audiolibrarian.domain.model.track import Track

log = getLogger(__name__)
ITUNES = "----:com.apple.iTunes"


class M4aFile(audiofile.AudioFile, extensions={".m4a"}):
    """AudioFile for M4A files."""

    def read_tags(self) -> release.OneTrack:
        """Read the tags and return a OneTrack object."""

        def get_str(key: str) -> str | None:
            # Return first element for the given key, utf8-decoded.
            if mut.get(key) is None:
                return None
            return str(mut.get(key)[0].decode("utf8"))

        def get_strl(key: str) -> record.ListF[str] | None:
            # Return all elements for a given key, utf8-decoded.
            if mut.get(key) is None:
                return None
            return record.ListF([x.decode("utf8") for x in mut.get(key)])

        def listf(key: str) -> record.ListF[str] | None:
            # Return a ListF object for a given key.
            if mut.get(key) is None:
                return None
            return record.ListF(mut.get(key))

        mut = self._mut_file

        front_cover = None
        if mut.get("covr"):
            cover = mut["covr"][0]
            # noinspection PyUnresolvedReferences
            mime = "image/png" if cover.imageformat == mutagen.mp4.AtomDataType.PNG else "image/jpg"
            front_cover = values.FrontCover(data=bytes(cover), mime=mime)
        medium_count = int(mut["disk"][0][1]) if mut.get("disk") else None
        medium_number = int(mut["disk"][0][0]) if mut.get("disk") else None
        track_count = int(mut["trkn"][0][1]) if mut.get("trkn") else None
        track_number = values.TrackNumber(int(mut["trkn"][0][0])) if mut.get("trkn") else None
        release_obj = (
            release.Release(
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
                                file_info=values.FileInfo(
                                    bitrate=mut.info.bitrate // 1000,
                                    bitrate_mode=enums.BitrateMode.CBR,
                                    path=self.filepath,
                                    type=enums.FileType.AAC,
                                ),
                                isrcs=get_strl(f"{ITUNES}:ISRC"),
                                musicbrainz_artist_ids=get_strl(f"{ITUNES}:MusicBrainz Artist Id"),
                                musicbrainz_release_track_id=get_str(f"{ITUNES}:MusicBrainz Release Track Id"),
                                musicbrainz_track_id=get_str(f"{ITUNES}:MusicBrainz Track Id"),
                                title=mut.get("\xa9nam", [None])[0],
                                track_number=values.TrackNumber(int(mut["trkn"][0][0])) if mut.get("trkn") else None,
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
                    values.People(
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
        if release_obj:
            release_obj = attrs.evolve(release_obj, source=enums.Source.TAGS)
        medium_pos = values.MediumPosition(number=medium_number, count=medium_count or 1) if medium_number else None
        return release.OneTrack(
            release=release_obj,
            medium_position=medium_pos,
            track_number=track_number,
        )

    def write_tags(self) -> None:
        """Write the tags."""

        def ff(text: int | str | None) -> bytes | None:
            if text is None:
                return None
            return mutagen.mp4.MP4FreeForm(bytes(str(text), "utf8"))  # type: ignore[no-untyped-call]

        def ffl(list_: list[str] | Any | None) -> record.ListF[bytes] | None:  # noqa: ANN401
            if not list_:
                return None
            return record.ListF([ff(x) for x in list_])

        # Note: We don't write "performers" to m4a files.
        release_, medium_number, medium, track_number, track = self._get_tag_sources()
        front_cover = None
        if (cover := release_.front_cover) is not None:
            # noinspection PyUnresolvedReferences
            image_format = mutagen.mp4.AtomDataType.PNG if cover.mime == "image/png" else mutagen.mp4.AtomDataType.JPEG
            front_cover = [
                mutagen.mp4.MP4Cover(cover.data, imageformat=image_format)  # type: ignore[no-untyped-call]
            ]
        tags_ = {
            f"{ITUNES}:ARRANGER": ffl(release_.people and release_.people.arrangers),
            f"{ITUNES}:ARTISTS": ffl(track.artists),
            f"{ITUNES}:ASIN": ffl(release_.asins),
            f"{ITUNES}:BARCODE": ffl(release_.barcodes),
            f"{ITUNES}:CATALOGNUMBER": ffl(release_.catalog_numbers),
            f"{ITUNES}:COMPOSER": ffl(release_.people and release_.people.composers),
            f"{ITUNES}:CONDUCTOR": ffl(release_.people and release_.people.conductors),
            f"{ITUNES}:DISCSUBTITLE": ffl(medium.titles),
            f"{ITUNES}:ENGINEER": ffl(release_.people and release_.people.engineers),
            f"{ITUNES}:ISRC": ffl(track.isrcs),
            f"{ITUNES}:LABEL": ffl(release_.labels),
            f"{ITUNES}:LYRICIST": ffl(release_.people and release_.people.lyricists),
            f"{ITUNES}:MEDIA": ffl(medium.formats),
            f"{ITUNES}:MIXER": ffl(release_.people and release_.people.mixers),
            f"{ITUNES}:MusicBrainz Album Artist Id": ffl(release_.musicbrainz_album_artist_ids),
            f"{ITUNES}:MusicBrainz Album Id": [ff(release_.musicbrainz_album_id)],
            f"{ITUNES}:MusicBrainz Album Release Country": ffl(release_.release_countries),
            f"{ITUNES}:MusicBrainz Album Status": ffl(release_.release_statuses),
            f"{ITUNES}:MusicBrainz Album Type": ffl(release_.release_types),
            f"{ITUNES}:MusicBrainz Artist Id": ffl(track.musicbrainz_artist_ids),
            f"{ITUNES}:MusicBrainz Release Group Id": [ff(release_.musicbrainz_release_group_id)],
            f"{ITUNES}:MusicBrainz Release Track Id": [ff(track.musicbrainz_release_track_id)],
            f"{ITUNES}:MusicBrainz Track Id": [ff(track.musicbrainz_track_id)],
            f"{ITUNES}:originaldate": [ff(release_.original_date)],
            f"{ITUNES}:originalyear": [ff(release_.original_year)],
            f"{ITUNES}:PRODUCER": ffl(release_.people and release_.people.producers),
            f"{ITUNES}:SCRIPT": [ff(release_.script)],
            f"{ITUNES}:WRITER": ffl(release_.people and release_.people.writers),
            "\xa9alb": [release_.album],
            "\xa9ART": [track.artist],
            "\xa9day": [release_.date],
            "\xa9gen": release_.genres,
            "\xa9nam": [track.title],
            "aART": release_.album_artists,
            "covr": front_cover,
            "disk": [(medium_number, release_.medium_count)] if medium_number else None,
            "soaa": release_.album_artists_sort,
            "soar": track.artists_sort,
            "trkn": [(track_number.value, medium.track_count)] if track_number else None,
        }
        tags_ = audiofile.Tags(tags_)

        for key, value in tags_.items():
            try:
                self._mut_file[key] = value
            except Exception:  # pragma: no cover
                log.critical("ERROR: %s %s", key, value)
                raise

        self._mut_file.save()
