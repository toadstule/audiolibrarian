"""AudioFile support for mp3 files."""

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
from typing import Any, no_type_check

import mutagen
import mutagen.id3

from audiolibrarian import audiofile, records

APIC = mutagen.id3.APIC
TXXX = mutagen.id3.TXXX
UFID = mutagen.id3.UFID
MB_UFID = "http://musicbrainz.org"


class Mp3File(audiofile.AudioFile, extensions={".mp3"}):
    """AudioFile for MP3 files."""

    @no_type_check  # The mutagen library doesn't provide type hints.
    def read_tags(self) -> records.OneTrack:
        """Read the tags and return a OneTrack object."""

        def get_l(key: str) -> records.ListF | None:
            if (value := mut.get(key)) is None:
                return None
            if "/" in str(value):
                return records.ListF(str(value).split("/"))
            return records.ListF(value)

        mut = self._mut_file
        front_cover = None
        if apic := mut.get("APIC:front cover", mut.get("APIC:front", mut.get("APIC:"))):
            front_cover = records.FrontCover(data=apic.data, desc=apic.desc, mime=apic.mime)
        tipl = mut["TIPL"].people if mut.get("TIPL") else []
        roles = ("arranger", "composer", "conductor", "engineer", "mix", "producer", "writer")
        medium_count = int(mut["TPOS"][0].split("/")[1]) if mut.get("TPOS") else None
        medium_number = int(mut["TPOS"][0].split("/")[0]) if mut.get("TPOS") else None
        track_count = int(mut["TRCK"][0].split("/")[1]) if mut.get("TRCK") else None
        track_number = int(mut["TRCK"][0].split("/")[0]) if mut.get("TRCK") else None
        bitrate = mut.info.bitrate // 1000
        bitrate_mode = records.BitrateMode.__members__[
            str(mut.info.bitrate_mode).rsplit(".", maxsplit=1)[-1]
        ]
        # Shortcut for common CBRs.
        if bitrate_mode == records.BitrateMode.UNKNOWN and bitrate in (128, 160, 192, 320):
            bitrate_mode = records.BitrateMode.CBR
        release = (
            records.Release(
                album=mut.get("TALB", [None])[0],
                album_artists=get_l("TPE2"),
                album_artists_sort=get_l("TSO2"),
                asins=get_l("TXXX:ASIN"),
                barcodes=get_l("TXXX:BARCODE"),
                catalog_numbers=get_l("TXXX:CATALOGNUMBER"),
                date=(mut.get("TDRC", [mutagen.id3.ID3TimeStamp("")])[0]).text or None,
                front_cover=front_cover,
                genres=get_l("TCON"),
                labels=get_l("TPUB"),
                media={
                    medium_number: records.Medium(
                        formats=get_l("TMED"),
                        titles=get_l("TSST"),
                        track_count=track_count,
                        tracks={
                            track_number: records.Track(
                                artist=mut.get("TPE1", [None])[0],
                                artists=get_l("TXXX:ARTISTS"),
                                artists_sort=get_l("TSOP"),
                                file_info=records.FileInfo(
                                    bitrate=bitrate,
                                    bitrate_mode=bitrate_mode,
                                    path=self.filepath,
                                    type=records.FileType.MP3,
                                ),
                                isrcs=get_l("TSRC"),
                                musicbrainz_artist_ids=get_l("TXXX:MusicBrainz Artist Id"),
                                musicbrainz_release_track_id=mut.get(
                                    "TXXX:MusicBrainz Release Track Id", [None]
                                )[0],
                                musicbrainz_track_id=mut.get(
                                    f"UFID:{MB_UFID}", UFID()
                                ).data.decode("utf8")
                                or None,
                                title=mut.get("TIT2", [None])[0],
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
                musicbrainz_album_artist_ids=get_l("TXXX:MusicBrainz Album Artist Id"),
                musicbrainz_album_id=mut.get("TXXX:MusicBrainz Album Id", [None])[0],
                musicbrainz_release_group_id=mut.get("TXXX:MusicBrainz Release Group Id", [None])[
                    0
                ],
                original_year=str((mut["TDOR"][0]).year) if mut.get("TDOR") else None,
                people=(
                    records.People(
                        arrangers=[name for role, name in tipl if role == "arranger"] or None,
                        composers=[name for role, name in tipl if role == "composer"] or None,
                        conductors=[name for role, name in tipl if role == "conductor"] or None,
                        engineers=[name for role, name in tipl if role == "engineer"] or None,
                        lyricists=get_l("TEXT"),
                        mixers=[name for role, name in tipl if role == "mix"] or None,
                        producers=[name for role, name in tipl if role == "producer"] or None,
                        performers=[
                            records.Performer(name=n, instrument=i)
                            for i, n in tipl
                            if i not in roles
                        ]
                        or None,
                        writers=[name for role, name in tipl if role == "writer"] or None,
                    )
                    or None
                ),
                release_countries=get_l("TXXX:MusicBrainz Album Release Country"),
                release_statuses=get_l("TXXX:MusicBrainz Album Status"),
                release_types=get_l("TXXX:MusicBrainz Album Type"),
                script=mut.get("TXXX:SCRIPT", [None])[0],
            )
            or None
        )
        if release:
            release.source = records.Source.TAGS
        return records.OneTrack(
            release=release, medium_number=medium_number, track_number=track_number
        )

    @no_type_check  # The mutagen library doesn't provide type hints.
    def write_tags(self) -> None:  # noqa: C901, PLR0912, PLR0915
        """Write the tags."""

        def slash(text: list[str] | records.ListF) -> str:
            return "/".join(text)

        release, medium_number, medium, track_number, track = self._get_tag_sources()
        tipl_people = (
            [["arranger", x] for x in (release.people and release.people.arrangers) or []]
            + [["composer", x] for x in (release.people and release.people.composers) or []]
            + [["conductor", x] for x in (release.people and release.people.conductors) or []]
            + [["engineer", x] for x in (release.people and release.people.engineers) or []]
            + [["mix", x] for x in (release.people and release.people.mixers) or []]
            + [["producer", x] for x in (release.people and release.people.producers) or []]
            + [
                [p.instrument, p.name]
                for p in (release.people and release.people.performers) or []
            ]
            + [["writer", x] for x in (release.people and release.people.writers) or []]
        )
        tags: list[mutagen.id3.Frame] = []
        # noinspection PyUnusedLocal
        tag: Any = None
        if tag := release.album:
            tags.append(mutagen.id3.TALB(encoding=1, text=tag))
        if tag := release.people and release.people.composers:
            tags.append(mutagen.id3.TCOM(encoding=1, text=slash(tag)))
        if tag := release.genres:
            tags.append(mutagen.id3.TCON(encoding=3, text=slash(tag)))
        if tag := release.original_year:
            tags.append(mutagen.id3.TDOR(encoding=0, text=str(tag)))
        if tag := release.date:
            tags.append(mutagen.id3.TDRC(encoding=0, text=tag))
        if tag := release.people and release.people.lyricists:
            tags.append(mutagen.id3.TEXT(encoding=1, text=slash(tag)))
        if people := tipl_people:
            tags.append(mutagen.id3.TIPL(encoding=1, people=people))
        if tag := track.title:
            tags.append(mutagen.id3.TIT2(encoding=1, text=tag))
        if tag := medium.formats:
            tags.append(mutagen.id3.TMED(encoding=1, text=slash(tag)))
        if tag := track.artist:
            tags.append(mutagen.id3.TPE1(encoding=1, text=tag))
        if tag := release.album_artists:
            tags.append(mutagen.id3.TPE2(encoding=1, text=slash(tag)))
        if tag := release.people and release.people.conductors:
            tags.append(mutagen.id3.TPE3(encoding=1, text=slash(tag)))
        if (num := medium_number) and (tag := release.medium_count):
            tags.append(mutagen.id3.TPOS(encoding=0, text=f"{num}/{tag}"))
        if tag := release.labels:
            tags.append(mutagen.id3.TPUB(encoding=1, text=slash(tag)))
        if (num := track_number) and (tag := medium.track_count):
            tags.append(mutagen.id3.TRCK(encoding=0, text=f"{num}/{tag}"))
        if tag := release.album_artists_sort:
            tags.append(mutagen.id3.TSO2(encoding=1, text=slash(tag)))
        if tag := track.artists_sort:
            tags.append(mutagen.id3.TSOP(encoding=1, text=slash(tag)))
        if tag := track.isrcs:
            tags.append(mutagen.id3.TSRC(encoding=1, text=slash(tag)))
        if tag := medium.titles:
            tags.append(mutagen.id3.TSST(encoding=1, text=slash(tag)))
        if tag := track.artists:
            tags.append(TXXX(encoding=1, desc="ARTISTS", text=slash(tag)))
        if tag := release.asins:
            tags.append(TXXX(encoding=1, desc="ASIN", text=slash(tag)))
        if tag := release.barcodes:
            tags.append(TXXX(encoding=1, desc="BARCODE", text=slash(tag)))
        if tag := release.catalog_numbers:
            tags.append(TXXX(encoding=1, desc="CATALOGNUMBER", text=slash(tag)))
        if tag := release.musicbrainz_album_artist_ids:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Artist Id", text=slash(tag)))
        if tag := release.musicbrainz_album_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Id", text=tag))
        if tag := release.release_countries:
            tags.append(
                TXXX(encoding=1, desc="MusicBrainz Album Release Country", text=slash(tag))
            )
        if tag := release.release_statuses:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Status", text=slash(tag)))
        if tag := release.release_types:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Type", text=slash(tag)))
        if tag := track.musicbrainz_artist_ids:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Artist Id", text=slash(tag)))
        if tag := release.musicbrainz_release_group_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Release Group Id", text=tag))
        if tag := track.musicbrainz_release_track_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Release Track Id", text=tag))
        if tag := release.script:
            tags.append(TXXX(encoding=1, desc="SCRIPT", text=tag))
        if tag := release.original_year:
            tags.append(TXXX(encoding=1, desc="originalyear", text=str(tag)))
        if id_ := track.musicbrainz_track_id:
            tags.append(UFID(owner=MB_UFID, data=bytes(id_, "utf8")))
        if (cover := release.front_cover) is not None:
            tags.append(
                APIC(encoding=0, mime=cover.mime, type=3, desc=cover.desc, data=cover.data)
            )

        try:
            id3 = mutagen.id3.ID3(self.filepath)
        except mutagen.id3.ID3NoHeaderError:
            self._mut_file.add_tags()
            self._mut_file.save()
            id3 = mutagen.id3.ID3(self.filepath)

        id3.delete()
        for tag in tags:
            id3.add(tag)
        id3.save()
        self._mut_file = mutagen.File(self.filepath.absolute())
