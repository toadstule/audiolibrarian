from typing import List

import mutagen
import mutagen.id3

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.records import (
    FrontCover,
    People,
    Performer,
    Release,
    Track,
    TrackView,
)

APIC = mutagen.id3.APIC
TXXX = mutagen.id3.TXXX
UFID = mutagen.id3.UFID
MB_UFID = "http://musicbrainz.org"


class Mp3File(AudioFile):
    extensions = (".mp3",)

    def read_tags(self) -> TrackView:
        def get_l(key) -> (List, None):
            if (value := mut.get(key)) is None:
                return None
            return list(value)

        mut = self._mut_file

        front_cover = None
        if apic := mut.get("APIC:front cover", mut.get("APIC:front", mut.get("APIC:"))):
            front_cover = FrontCover(data=apic.data, desc=apic.desc, mime=apic.mime)
        tipl = mut["TIPL"].people if mut.get("TIPL") else []
        roles = ("engineer", "mix", "producer")

        release = Release(
            album=mut.get("TALB", [None])[0],
            album_artists=get_l("TPE2"),
            album_artists_sort=get_l("TSO2"),
            asins=get_l("TXXX:ASIN"),
            barcodes=get_l("TXXX:BARCODE"),
            catalog_numbers=get_l("TXXX:CATALOGNUMBER"),
            date=(mut.get("TDRC", [mutagen.id3.ID3TimeStamp("")])[0]).text or None,
            disc_number=int(mut["TPOS"][0].split("/")[0]) if mut.get("TPOS") else None,
            disc_total=int(mut["TPOS"][0].split("/")[1]) if mut.get("TPOS") else None,
            front_cover=front_cover,
            genres=get_l("TCON"),
            labels=get_l("TPUB"),
            media=get_l("TMED"),
            musicbrainz_album_artist_ids=get_l("TXXX:MusicBrainz Album Artist Id"),
            musicbrainz_album_id=mut.get("TXXX:MusicBrainz Album Id", [None])[0],
            musicbrainz_release_group_id=mut.get("TXXX:MusicBrainz Release Group Id", [None])[0],
            original_year=str((mut["TDOR"][0]).year) if mut.get("TDOR") else None,
            people=(
                People(
                    engineers=[name for role, name in tipl if role == "engineer"] or None,
                    lyricists=get_l("TEXT"),
                    mixers=[name for role, name in tipl if role == "mix"] or None,
                    producers=[name for role, name in tipl if role == "producer"] or None,
                    performers=[Performer(n, r) for r, n in tipl if r not in roles] or None,
                )
                or None
            ),
            release_countries=get_l("TXXX:MusicBrainz Album Release Country"),
            release_statuses=get_l("TXXX:MusicBrainz Album Status"),
            release_types=get_l("TXXX:MusicBrainz Album Type"),
            script=mut.get("TXXX:SCRIPT", [None])[0],
            track_total=int(mut["TRCK"][0].split("/")[1]) if mut.get("TRCK") else None,
        )
        track = Track(
            artist=mut.get("TPE1", [None])[0],
            artists=get_l("TXXX:ARTISTS"),
            artists_sort=get_l("TSOP"),
            isrcs=get_l("TSRC"),
            musicbrainz_artist_ids=get_l("TXXX:MusicBrainz Artist Id"),
            musicbrainz_release_track_id=mut.get("TXXX:MusicBrainz Release Track Id", [None])[0],
            musicbrainz_track_id=mut.get(f"UFID:{MB_UFID}", UFID()).data.decode("utf8") or None,
            title=mut.get("TIT2", [None])[0],
            track_number=int(mut["TRCK"][0].split("/")[0]) if mut.get("TRCK") else None,
        )

        return TrackView(release=release, track=track)

    def write_tags(self) -> None:
        release = self._track_view.release
        track = self._track_view.track

        tipl_people = (
            [["engineer", x] for x in release.people and release.people.engineers or []]
            + [["mix", x] for x in release.people and release.people.mixers or []]
            + [["producer", x] for x in release.people and release.people.producers or []]
            + [[p.instrument, p.name] for p in release.people and release.people.performers or []]
        )
        tags = []
        if t := release.album:
            tags.append(mutagen.id3.TALB(encoding=1, text=t))
        if t := release.genres:
            tags.append(mutagen.id3.TCON(encoding=3, text=t))
        if t := release.original_year:
            tags.append(mutagen.id3.TDOR(encoding=0, text=str(t)))
        if t := release.date:
            tags.append(mutagen.id3.TDRC(encoding=0, text=t))
        if t := release.people and release.people.lyricists:
            tags.append(mutagen.id3.TEXT(encoding=1, text=t))
        if p := tipl_people:
            tags.append(mutagen.id3.TIPL(encoding=1, people=p))
        if t := track.title:
            tags.append(mutagen.id3.TIT2(encoding=1, text=t))
        if t := release.media:
            tags.append(mutagen.id3.TMED(encoding=1, text=t))
        if t := track.artist:
            tags.append(mutagen.id3.TPE1(encoding=1, text=t))
        if t := release.album_artists:
            tags.append(mutagen.id3.TPE2(encoding=1, text=t))
        if (n := release.disc_number) and (t := release.disc_total):
            tags.append(mutagen.id3.TPOS(encoding=0, text=f"{n}/{t}"))
        if t := release.labels:
            tags.append(mutagen.id3.TPUB(encoding=1, text=t))
        if (n := track.track_number) and (t := release.track_total):
            tags.append(mutagen.id3.TRCK(encoding=0, text=f"{n}/{t}"))
        if t := release.album_artists_sort:
            tags.append(mutagen.id3.TSO2(encoding=1, text=t))
        if t := track.artists_sort:
            tags.append(mutagen.id3.TSOP(encoding=1, text=t))
        if t := track.isrcs:
            tags.append(mutagen.id3.TSRC(encoding=1, text=t))
        if t := track.artists:
            tags.append(TXXX(encoding=1, desc="ARTISTS", text=t))
        if t := release.asins:
            tags.append(TXXX(encoding=1, desc="ASIN", text=t))
        if t := release.barcodes:
            tags.append(TXXX(encoding=1, desc="BARCODE", text=t))
        if t := release.catalog_numbers:
            tags.append(TXXX(encoding=1, desc="CATALOGNUMBER", text=t))
        if t := release.musicbrainz_album_artist_ids:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Artist Id", text=t))
        if t := release.musicbrainz_album_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Id", text=t))
        if t := release.release_countries:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Release Country", text=t))
        if t := release.release_statuses:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Status", text=t))
        if t := release.release_types:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Album Type", text=t))
        if t := track.musicbrainz_artist_ids:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Artist Id", text=t))
        if t := release.musicbrainz_release_group_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Release Group Id", text=t))
        if t := track.musicbrainz_release_track_id:
            tags.append(TXXX(encoding=1, desc="MusicBrainz Release Track Id", text=t))
        if t := release.script:
            tags.append(TXXX(encoding=1, desc="SCRIPT", text=t))
        if t := release.original_year:
            tags.append(TXXX(encoding=1, desc="originalyear", text=str(t)))
        if d := track.musicbrainz_track_id:
            tags.append(UFID(owner=MB_UFID, data=bytes(d, "utf8")))
        if (c := release.front_cover) is not None:
            tags.append(APIC(encoding=0, mime=c.mime, type=3, desc=c.desc, data=c.data))

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
