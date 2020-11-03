from typing import List

from mutagen.mp4 import AtomDataType, MP4Cover, MP4FreeForm

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audioinfo import (
    FrontCover,
    Info,
    RelationInfo,
    ReleaseInfo,
    TrackInfo,
)
from audiolibrarian.audiofile.tags import Tags

ITUNES = "----:com.apple.iTunes"


class M4aFile(AudioFile):
    extensions = (".m4a",)

    def read_tags(self) -> Info:
        def get_str(key) -> (str, None):
            # Return first element for the given key, utf8-decoded.
            if mut.get(key) is None:
                return
            return mut.get(key)[0].decode("utf8")

        def get_strl(key) -> (List[str], None):
            # Return all elements for a given key, utf8-decoded.
            if mut.get(key) is None:
                return None
            return [x.decode("utf8") for x in mut.get(key)]

        mut = self._mut_file

        front_cover = None
        if mut.get("covr"):
            cover = mut["covr"][0]
            mime = "image/png" if cover.imageformat == AtomDataType.PNG else "image/jpg"
            front_cover = FrontCover(data=bytes(cover), mime=mime)

        release_info = ReleaseInfo(
            album=mut.get("\xa9alb", [None])[0],
            album_artists=mut.get("aART"),
            album_artists_sort=mut.get("soaa"),
            asins=get_strl(f"{ITUNES}:ASIN"),
            barcodes=get_strl(f"{ITUNES}:BARCODE"),
            catalog_numbers=get_strl(f"{ITUNES}:CATALOGNUMBER"),
            date=mut.get("\xa9day", [None])[0],
            disc_number=int(mut["disk"][0][0]) if mut.get("disk") else None,
            disc_total=int(mut["disk"][0][1]) if mut.get("disk") else None,
            front_cover=front_cover,
            genres=mut.get("\xa9gen"),
            labels=get_strl(f"{ITUNES}:LABEL"),
            media=get_strl(f"{ITUNES}:MEDIA"),
            musicbrainz_album_artist_ids=get_strl(f"{ITUNES}:MusicBrainz Album Artist Id"),
            musicbrainz_album_id=get_str(f"{ITUNES}:MusicBrainz Album Id"),
            musicbrainz_release_group_id=get_str(f"{ITUNES}:MusicBrainz Release Group Id"),
            original_date=get_str(f"{ITUNES}:originaldate"),
            original_year=int(get_str(f"{ITUNES}:originalyear") or 0) or None,
            release_countries=get_strl(f"{ITUNES}:MusicBrainz Album Release Country"),
            release_statuses=get_strl(f"{ITUNES}:MusicBrainz Album Status"),
            release_types=get_strl(f"{ITUNES}:MusicBrainz Album Type"),
            script=get_str(f"{ITUNES}:SCRIPT"),
            track_total=int(mut["trkn"][0][1]) if mut.get("trkn") else None,
        )
        track_info = TrackInfo(
            artist=mut.get("\xa9ART", [None])[0],
            artists=get_strl(f"{ITUNES}:ARTISTS"),
            artists_sort=mut.get("soar"),
            isrcs=get_strl(f"{ITUNES}:ISRC"),
            musicbrainz_artist_ids=get_strl(f"{ITUNES}:MusicBrainz Artist Id"),
            musicbrainz_release_track_id=get_str(f"{ITUNES}:MusicBrainz Release Track Id"),
            musicbrainz_track_id=get_str(f"{ITUNES}:MusicBrainz Track Id"),
            title=mut.get("\xa9nam", [None])[0],
            track_number=int(mut["trkn"][0][0]) if mut.get("trkn") else None,
        )
        relation_info = RelationInfo(
            engineers=get_strl(f"{ITUNES}:ENGINEER"),
            lyricists=get_strl(f"{ITUNES}:LYRICIST"),
            mixers=get_strl(f"{ITUNES}:MIXER"),
            producers=get_strl(f"{ITUNES}:PRODUCER"),
            performers=None,
        )
        return Info(relation_info=relation_info, release_info=release_info, track_info=track_info)

    def write_tags(self) -> None:
        def ff(s: (str, int, None)) -> (bytes, None):
            if s is None:
                return
            return MP4FreeForm(bytes(str(s), "utf8"))

        def ffl(list_: (List[str], None)) -> (List[bytes], None):
            if not list_:
                return
            return [ff(x) for x in list_]

        # Note: We don't write "performers" to m4a files.
        relation = self._info.relation_info
        release = self._info.release_info
        track = self._info.track_info

        front_cover = None
        if (c := release.front_cover) is not None:
            image_format = AtomDataType.PNG if c.mime == "image/png" else AtomDataType.JPEG
            front_cover = [MP4Cover(c.data, imageformat=image_format)]

        tags = {
            f"{ITUNES}:ARTISTS": ffl(track.artists),
            f"{ITUNES}:ASIN": ffl(release.asins),
            f"{ITUNES}:BARCODE": ffl(release.barcodes),
            f"{ITUNES}:CATALOGNUMBER": ffl(release.catalog_numbers),
            f"{ITUNES}:ENGINEER": ffl(relation.engineers),
            f"{ITUNES}:ISRC": ffl(track.isrcs),
            f"{ITUNES}:LABEL": ffl(release.labels),
            f"{ITUNES}:LYRICIST": ffl(relation.lyricists),
            f"{ITUNES}:MEDIA": ffl(release.media),
            f"{ITUNES}:MIXER": ffl(relation.mixers),
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
            f"{ITUNES}:PRODUCER": ffl(relation.producers),
            f"{ITUNES}:SCRIPT": [ff(release.script)],
            "\xa9alb": [release.album],
            "\xa9ART": [track.artist],
            "\xa9day": [release.date],
            "\xa9gen": release.genres,
            "\xa9nam": [track.title],
            "aART": release.album_artists,
            "covr": front_cover,
            "disk": [(release.disc_number, release.disc_total)] if release.disc_number else None,
            "soaa": release.album_artists_sort,
            "soar": track.artists_sort,
            "trkn": [(track.track_number, release.track_total)] if track.track_number else None,
        }
        tags = Tags(tags)

        for k, v in tags.items():
            try:
                self._mut_file[k] = v
            except Exception:
                print("ERROR:", k, v)
                raise

        self._mut_file.save()
