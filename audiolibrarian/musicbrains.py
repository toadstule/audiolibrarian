import musicbrainzngs
from fuzzywuzzy import fuzz

from audiolibrarian.audioinfo import AudioInfo

musicbrainzngs.set_useragent("jib-audio", "0.1", "steve@jibson.com")
genres = ["alternative", "alternative rock", "country", "pop", "progressive rock", "rock"]


class MusicBrainsInfo(AudioInfo):
    def _get_artist_id(self):
        artist = self._input_artist
        artist_list = musicbrainzngs.search_artists(artist)["artist-list"]
        self._pprint("ARTISTS", artist_list)
        return artist_list[0]["id"]

    def _get_genre(self, release_group_tags):
        genre = None
        self._pprint("RELEASE_GROUP_TAGS", release_group_tags)
        if release_group_tags:
            for genre_tag in reversed(sorted(release_group_tags, key=lambda x: x["count"])):
                if genre_tag["name"].lower() in genres:
                    genre = genre_tag["name"].title()
                    break
        if genre is None:
            genre = input("Genre not found; enter the genre [Alternative]: ") or "Alternative"
        return genre

    def _get_release_group_ids(self, artist_id):
        album_l = self._input_album.lower()
        release_group_list = musicbrainzngs.browse_release_groups(artist=artist_id, limit=500)[
            "release-group-list"
        ]
        self._pprint("RELEASE_GROUPS", release_group_list)
        return [
            rg["id"]
            for rg in release_group_list
            if rg.get("primary-type") == "Album" and fuzz.ratio(album_l, rg["title"].lower()) > 80
        ]

    @staticmethod
    def _prompt_release_id(release_group_ids):
        print(
            "\n\nWe found the following release group(s). Use the link(s) below to "
            "find the release ID that best matches the audio files.\n"
        )
        for release_group_id in release_group_ids:
            print(f"https://musicbrainz.org/release-group/{release_group_id}")

        while True:
            release_input = input("\nRelease ID or URL: ")
            try:
                release_id = release_input.split("/")[-1]
            except ValueError:
                pass
            else:
                return release_id

    def _update(self):
        artist_id = self._get_artist_id()
        print("ARTIST_ID:", artist_id)
        artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
        self._pprint("ARTIST", artist)
        release_group_ids = self._get_release_group_ids(artist_id)
        print("RELEASE_GROUPS:", release_group_ids)
        release_id = self._prompt_release_id(release_group_ids)
        release = musicbrainzngs.get_release_by_id(
            release_id,
            includes=["artist-credits", "isrcs", "labels", "recordings", "release-groups", "tags"],
        )["release"]
        release_group = release["release-group"]
        medium = release["medium-list"][0]
        self._pprint("RELEASE", release)

        self.artist = artist["name"]
        self.artist_sort_name = artist["sort-name"]
        self.album = release["title"].replace("’", "'")
        self.genre = self._get_genre(release_group.get("tag-list"))
        self.year = release["release-event-list"][0]["date"]
        self.original_year = release_group.get("first-release-date", "").split("-")[0] or self.year

        self.tracks = []
        for t in medium["track-list"]:
            r = t["recording"]
            ac = t.get("artist-credit") or r["artist-credit"]
            track = {
                "number": t["position"],
                "title": (t.get("title") or r["title"]).replace("’", "'"),
                "id": t["id"],
                "recording_id": r["id"],
                "isrc": "/".join(r.get("isrc-list", [])),
                "artist_id": "/".join([a["artist"]["id"] for a in ac if isinstance(a, dict)]),
                "artist_names": "/".join([a["artist"]["name"] for a in ac if isinstance(a, dict)]),
            }
            artist_names = ""
            artist_sort_names = ""
            for a in ac:
                if isinstance(a, dict):
                    artist_names += a["artist"]["name"]
                    artist_sort_names += a["artist"]["sort-name"]
                else:
                    artist_names += a
                    artist_sort_names += a
            track["artist"] = artist_names
            track["artist_sort_order"] = artist_sort_names

            self.tracks.append(track)

        if release["cover-art-archive"]["front"] == "true":
            self.front_cover = musicbrainzngs.get_image_front(release_id, size=500)

        release_type = release_group["primary-type"]
        if release_group["type"] != release_type:
            release_type += f"/{release_group['type']}"

        self.disc_number = medium["position"]
        self.media = medium["format"]
        self.organization = "/".join([x["label"]["name"] for x in release["label-info-list"]])
        self.barcode = release["barcode"]
        self.asin = release.get("asin", "")
        self.album_type = release_type.lower()
        self.album_status = release["status"].lower()
        self.country = release["country"]
        self.catalog_number = release["label-info-list"][0].get("catalog-number", "")
        self.mb_artist_id = artist_id
        self.mb_release_group_id = release_group["id"]
        self.mb_release_id = release_id
