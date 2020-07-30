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
            genre = input("Unable to determine genre; enter the genre: ")
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
            if rg["primary-type"] == "Album" and fuzz.ratio(album_l, rg["title"]) > 80
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
            release_id, includes=["recordings", "release-groups", "tags"]
        )["release"]
        release_group = release["release-group"]
        medium = release["medium-list"][0]
        self._pprint("RELEASE", release)

        self.artist = artist["name"]
        self.artist_sort_name = artist["sort-name"]
        self.album = release["title"]
        self.genre = self._get_genre(
            release_group.get("tag-list"),
            # medium.get("track-list", [{}])[0].get("recording", {}).get("tag-list"),
        )

        release_group_year = release_group.get("first-release-date", "").split("-")[0]
        release_year = release["release-event-list"][0]["date"]
        self.year = release_group_year or release_year
        if release_group_year and self.year != release_year:
            self.comments.append(f"Year: {release_year}")

        self.tracks = [
            {"number": t["position"].zfill(2), "title": t["recording"]["title"]}
            for t in medium["track-list"]
        ]

        if release["cover-art-archive"]["front"] == "true":
            self.front_cover = musicbrainzngs.get_image_front(release_id, size=500)
