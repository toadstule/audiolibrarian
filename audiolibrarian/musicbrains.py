import time

import musicbrainzngs
import requests
from fuzzywuzzy import fuzz
from requests.auth import HTTPDigestAuth

from audiolibrarian.audioinfo import AudioInfo

musicbrainzngs.set_useragent("audiolibrarian", "0.1", "steve@jibson.com")


class MusicBrainsSession:
    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPDigestAuth("toadstule", "***REMOVED***")
        self._session.headers.update({"User-Agent": "audiolibrarian/0.1/steve@jibson.com"})

    def _get(self, path, params=None):
        # Used for direct API calls; those not supported by the python library
        path = path.lstrip("/")
        url = f"https://musicbrainz.org/ws/2/{path}"
        params["fmt"] = "json"
        r = self._session.get(url, params=params)
        while r.status_code == 503:
            print("Waiting due to throttling...")
            time.sleep(30)
            r = self._session.get(url, params=params)
        assert r.status_code == 200, f"{r.status_code} - {url}"
        return r.json()

    def get_artist_by_id(self, artist_id, includes=None):
        params = {}
        if includes is not None:
            params["inc"] = "+".join(includes)
        return self._get(f"artist/{artist_id}", params=params)

    def get_release_group_by_id(self, release_group_id, includes=None):
        params = {}
        if includes is not None:
            params["inc"] = "+".join(includes)
        return self._get(f"release-group/{release_group_id}", params=params)


class MusicBrainsInfo(AudioInfo):
    def __init__(self, search_data, verbose=False):
        self._session = MusicBrainsSession()
        super().__init__(search_data, verbose)

    def _get_artist_id(self):
        artist = self._search_data.artist
        artist_list = musicbrainzngs.search_artists(artist)["artist-list"]
        self._pprint("ARTISTS", artist_list)
        return artist_list[0]["id"]

    def _get_genre(self, release_group_id, artist_id):
        # Try to find the genre using the following methods (in order):
        # - release-group user-genres
        # - artist user-genres
        # - release-group genres
        # - release-group tags
        # - user input

        # user-genres and genres are not supported with the python library
        rg = self._session.get_release_group_by_id(
            release_group_id, includes=["genres", "user-genres"]
        )
        self._pprint("RELEASE_GROUP_GENRES", rg)
        at = self._session.get_artist_by_id(artist_id, includes=["genres", "user-genres"])
        self._pprint("ARTIST_GENRES", at)
        if rg["user-genres"]:
            return rg["user-genres"][0]["name"]
        if at["user-genres"]:
            return at["user-genres"][0]["name"]
        if rg["genres"]:
            return [g["name"] for g in reversed(sorted(rg["genres"], key=lambda x: x["count"]))][0]
        if at["genres"]:
            return [g["name"] for g in reversed(sorted(at["genres"], key=lambda x: x["count"]))][0]
        return input("Genre not found; enter the genre [Alternative]: ") or "Alternative"

    def _get_release_group_ids(self, artist_id):
        album_l = self._search_data.album.lower()
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
        artist_id = None
        release_id = None
        if self._search_data.mb_artist_id and self._search_data.mb_release_id:
            artist_id = self._search_data.mb_artist_id
            release_id = self._search_data.mb_release_id
        elif self._search_data.disc_id:
            result = musicbrainzngs.get_releases_by_discid(
                self._search_data.disc_id, includes=["artists"]
            )
            self._pprint("DISC", result)
            if result.get("disc"):
                artist_id = result["disc"]["release-list"][0]["artist-credit"][0]["artist"]["id"]
                release_id = result["disc"]["release-list"][0]["id"]
            elif result.get("cdstub"):
                print("A CD Stub exists for this disc, but no disc.")
        if not artist_id:
            artist_id = self._get_artist_id()
        print("ARTIST_ID:", artist_id)
        artist = musicbrainzngs.get_artist_by_id(artist_id)["artist"]
        self._pprint("ARTIST", artist)
        if release_id:
            print(f"https://musicbrainz.org/release/{release_id}")
        else:
            release_group_ids = self._get_release_group_ids(artist_id)
            print("RELEASE_GROUPS:", release_group_ids)
            release_id = self._prompt_release_id(release_group_ids)
        release = musicbrainzngs.get_release_by_id(
            release_id,
            includes=["artist-credits", "isrcs", "labels", "recordings", "release-groups", "tags"],
        )["release"]
        release_group = release["release-group"]
        medium = release["medium-list"][int(self._search_data.disc_number) - 1]
        self._pprint("RELEASE", release)

        self.artist = artist["name"]
        self.artist_sort_name = artist["sort-name"]
        self.album = release["title"].replace("’", "'")
        self.genre = self._get_genre(release_group["id"], artist_id).title()
        self.year = release["release-event-list"][0].get("date") or input("Release year: ")
        self.original_date = release_group.get("first-release-date", "")
        self.original_year = self.original_date.split("-")[0] or self.year

        self.tracks = []
        for t in medium["track-list"]:
            r = t["recording"]
            ac = t.get("artist-credit") or r["artist-credit"]
            track = {
                "number": t["position"],
                "title": (t.get("title") or r["title"]).replace("’", "'"),
                "id": t["id"],
                "recording_id": r["id"],
                "isrc": r.get("isrc-list", []),
                "artist_names": "/".join([a["artist"]["name"] for a in ac if isinstance(a, dict)]),
            }
            artist_names = ""
            artist_names_list = []
            artist_sort_names = ""
            artist_ids = []
            for a in ac:
                if isinstance(a, dict):
                    artist_names += a["artist"]["name"]
                    artist_names_list.append(a["artist"]["name"])
                    artist_sort_names += a["artist"]["sort-name"]
                    artist_ids.append(a["artist"]["id"])
                else:
                    artist_names += a
                    artist_sort_names += a
            track["artist"] = artist_names
            track["artist_list"] = artist_names_list
            track["artist_sort_order"] = artist_sort_names
            track["artist_id"] = artist_ids

            self.tracks.append(track)

        if release["cover-art-archive"]["front"] == "true":
            self.front_cover = musicbrainzngs.get_image_front(release_id, size=500)

        self.album_type = [release_group["primary-type"].lower()]
        if release_group["type"].lower() != self.album_type[0]:
            self.album_type.append(release_group["type"].lower())

        self.disc_number = medium["position"]
        self.media = medium.get("format", "")
        self.organization = [x["label"]["name"] for x in release["label-info-list"]]
        self.barcode = release.get("barcode", "")
        self.asin = release.get("asin", "")
        self.album_status = release.get("status", "").lower()
        self.catalog_number = (release.get("label-info-list") or [{}])[0].get("catalog-number", "")
        self.country = release.get("country", "")
        self.mb_artist_id = artist_id
        self.mb_release_group_id = release_group["id"]
        self.mb_release_id = release_id
