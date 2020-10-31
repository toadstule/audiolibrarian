from typing import List

from mutagen.mp4 import MP4FreeForm

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.audioinfo import (
    Info,
    Performer,
    RelationInfo,
    ReleaseInfo,
    TrackInfo,
)


class M4aFile(AudioFile):
    extensions = (".m4a",)

    _missing_tags_if_blank = (
        "----:com.apple.iTunes:ASIN",
        "----:com.apple.iTunes:BARCODE",
        "----:com.apple.iTunes:CATALOGNUMBER",
        "----:com.apple.iTunes:ENGINEER",
        "----:com.apple.iTunes:ISRC",
        "----:com.apple.iTunes:LYRICIST",
        "----:com.apple.iTunes:MIXER",
        "----:com.apple.iTunes:PRODUCER",
        "\xa9gen",
    )

    def read_tags(self) -> Info:
        mut = self._mut_file
        # print("> MUT_FILE:", self._mut_file)

        def get_str(key) -> str:
            return [x.decode("utf-8") for x in mut.get(key, [b""])][0]

        def get_strl(key) -> List[str]:
            return [x.decode("utf8") for x in mut.get(key, [])]

        release_info = ReleaseInfo(
            album=mut.get("\xa9alb", [""])[0],
            album_artists=mut.get("aART", []),
            album_artists_sort=mut.get("soaa", []),
            asins=get_strl("----:com.apple.iTunes:ASIN"),
            barcodes=get_strl("----:com.apple.iTunes:BARCODE"),
            catalog_numbers=get_strl("----:com.apple.iTunes:CATALOGNUMBER"),
            date=mut.get("\xa9day", [""])[0],
            disc_number=int(mut.get("disk", [("1", "0")])[0][0]),
            disc_total=int(mut.get("disk", [("1", "0")])[0][1]),
            genres=mut.get("\xa9gen", []),
            labels=get_strl("----:com.apple.iTunes:LABEL"),
            media=get_strl("----:com.apple.iTunes:MEDIA"),
            musicbrainz_album_artist_ids=get_strl(
                "----:com.apple.iTunes:MusicBrainz Album Artist Id"
            ),
            musicbrainz_album_id=get_str("----:com.apple.iTunes:MusicBrainz Album Id"),
            musicbrainz_release_group_id=get_str(
                "----:com.apple.iTunes:MusicBrainz Release Group Id"
            ),
            original_date=get_str("----:com.apple.iTunes:originaldate"),
            original_year=int(get_str("----:com.apple.iTunes:originalyear") or 0),
            release_countries=get_strl("----:com.apple.iTunes:MusicBrainz Album Release Country"),
            release_statuses=get_strl("----:com.apple.iTunes:MusicBrainz Album Status"),
            release_types=get_strl("----:com.apple.iTunes:MusicBrainz Album Type"),
            script=get_str("----:com.apple.iTunes:SCRIPT"),
            track_total=int(mut.get("trkn", [("1", "0")])[0][1]),
        )
        track_info = TrackInfo(
            artist=mut.get("\xa9ART", [""])[0],
            artists=get_strl("----:com.apple.iTunes:ARTISTS"),
            artists_sort=mut.get("soar", []),
            isrcs=get_strl("----:com.apple.iTunes:ISRC"),
            musicbrainz_artist_ids=get_strl("----:com.apple.iTunes:MusicBrainz Artist Id"),
            musicbrainz_release_track_id=get_str(
                "----:com.apple.iTunes:MusicBrainz Release Track Id"
            ),
            musicbrainz_track_id=get_str("----:com.apple.iTunes:MusicBrainz Track Id"),
            title=mut.get("\xa9nam", [""])[0],
            track_number=int(mut.get("trkn", [("1", "0")])[0][0]),
        )
        relation_info = RelationInfo()
        _ = Performer
        return Info(relation_info=relation_info, release_info=release_info, track_info=track_info)

    def write_tags(self) -> None:
        relation = self._info.relation_info
        release = self._info.release_info
        track = self._info.track_info

        def ff(s: (str, int)) -> bytes:
            return MP4FreeForm(bytes(str(s), "utf8"))

        def ffl(list_: List[str]) -> List[bytes]:
            return [ff(x) for x in list_]

        tags = {
            "----:com.apple.iTunes:ARTISTS": ffl(track.artists),
            "----:com.apple.iTunes:ASIN": ffl(release.asins),
            "----:com.apple.iTunes:BARCODE": ffl(release.barcodes),
            "----:com.apple.iTunes:CATALOGNUMBER": ffl(release.catalog_numbers),
            "----:com.apple.iTunes:ENGINEER": ffl(relation.engineers),
            "----:com.apple.iTunes:ISRC": ffl(track.isrcs),
            "----:com.apple.iTunes:LABEL": ffl(release.labels),
            "----:com.apple.iTunes:LYRICIST": ffl(relation.lyricists),
            "----:com.apple.iTunes:MEDIA": ffl(release.media),
            "----:com.apple.iTunes:MIXER": ffl(relation.mixers),
            "----:com.apple.iTunes:MusicBrainz Album Artist Id": ffl(
                release.musicbrainz_album_artist_ids
            ),
            "----:com.apple.iTunes:MusicBrainz Album Id": [ff(release.musicbrainz_album_id)],
            "----:com.apple.iTunes:MusicBrainz Album Release Country": ffl(
                release.release_countries
            ),
            "----:com.apple.iTunes:MusicBrainz Album Status": ffl(release.release_statuses),
            "----:com.apple.iTunes:MusicBrainz Album Type": ffl(release.release_types),
            "----:com.apple.iTunes:MusicBrainz Artist Id": ffl(track.musicbrainz_artist_ids),
            "----:com.apple.iTunes:MusicBrainz Release Group Id": [
                ff(release.musicbrainz_release_group_id)
            ],
            "----:com.apple.iTunes:MusicBrainz Release Track Id": [
                ff(track.musicbrainz_release_track_id)
            ],
            "----:com.apple.iTunes:MusicBrainz Track Id": [ff(track.musicbrainz_track_id)],
            "----:com.apple.iTunes:originaldate": [ff(release.original_date)],
            "----:com.apple.iTunes:originalyear": [ff(release.original_year)],
            "----:com.apple.iTunes:PRODUCER": ffl(relation.producers),
            "----:com.apple.iTunes:SCRIPT": [ff(release.script)],
            "\xa9alb": [release.album],
            "\xa9ART": [track.artist],
            "\xa9day": [release.date],
            "\xa9gen": release.genres,
            "\xa9nam": [track.title],
            "aART": release.album_artists,
            "disk": [(release.disc_number, release.disc_total)],
            "soaa": release.album_artists_sort,
            "soar": track.artists_sort,
            "trkn": [(track.track_number, release.track_total)],
        }
        for tag in self._missing_tags_if_blank:
            if tag in tags and not tags[tag]:
                del tags[tag]

        for k, v in tags.items():
            self._mut_file[k] = v

        # TO DO
        # if info.front_cover:
        #     cover = mutagen.mp4.MP4Cover(info.front_cover)
        #     song["covr"] = [cover]

        self._mut_file.save()
