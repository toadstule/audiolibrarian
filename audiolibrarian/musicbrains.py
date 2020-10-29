import time
from typing import List, Tuple

import musicbrainzngs
import requests
from fuzzywuzzy import fuzz
from requests.auth import HTTPDigestAuth

from audiolibrarian import text
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

    # def _get_artist_id(self):
    #     artist = self._search_data.artist
    #     artist_list = musicbrainzngs.search_artists(artist)["artist-list"]
    #     self._pprint("ARTISTS", artist_list)
    #     return artist_list[0]["id"]

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

    def _prompt_release_id(self, release_group_ids):
        print(
            "\n\nWe found the following release group(s). Use the link(s) below to "
            "find the release ID that best matches the audio files.\n"
        )
        for release_group_id in release_group_ids:
            print(f"https://musicbrainz.org/release-group/{release_group_id}")

        return self._prompt_uuid("\nRelease ID or URL: ")

    @staticmethod
    def _process_artist_credit(artist_credit: list) -> Tuple[str, List[str], str, List[str]]:
        # Get artist info from an artist-credit
        artist_names = ""
        artist_names_list = []
        artist_sort_names = ""
        artist_ids = []
        for a in artist_credit:
            if isinstance(a, dict):
                artist_names += a.get("name") or a["artist"]["name"]
                artist_names_list.append(a.get("name") or a["artist"]["name"])
                artist_sort_names += a["artist"]["sort-name"]
                artist_ids.append(a["artist"]["id"])
            else:
                artist_names += a
                artist_sort_names += a
        return artist_names, artist_names_list, artist_sort_names, artist_ids

    @staticmethod
    def _process_relationships(relationships: list) -> List[Tuple[str, str]]:
        result = []
        for r in relationships:
            value = r["artist"]["name"]
            type_ = r["type"].lower()
            if type_ == 'instrument':
                key = "PERFORMER"
                value = f"{r['artist']['name']} ({','.join(r['attribute-list'])})"
            elif type_ == "mix":
                key = "MIXER"
            elif type_ == "vocal":
                key = "PERFORMER"
                value = f"{r['artist']['name']} (lead vocals)"
            else:
                key = r["type"].upper()
            result.append((key, value))
        return result

    @staticmethod
    def _prompt_uuid(prompt):
        while True:
            uuid = text.get_uuid(input(prompt))
            if uuid is not None:
                return uuid

    def _update(self):
        release_id = self._search_data.mb_release_id

        if not release_id and self._search_data.disc_id:
            result = musicbrainzngs.get_releases_by_discid(
                self._search_data.disc_id, includes=["artists"]
            )
            self._pprint("DISC", result)
            if result.get("disc"):
                release_id = result["disc"]["release-list"][0]["id"]
            elif result.get("cdstub"):
                print("A CD Stub exists for this disc, but no disc.")

        if release_id:
            print(f"https://musicbrainz.org/release/{release_id}")
        # elif self._search_data.album:  TODO -- make this work without artist_id
        #     release_group_ids = self._get_release_group_ids(artist_id)
        #     print("RELEASE_GROUPS:", release_group_ids)
        #     release_id = self._prompt_release_id(release_group_ids)
        else:
            release_id = self._prompt_uuid("Musicbrainz Release ID: ")
        release = musicbrainzngs.get_release_by_id(
            release_id,
            includes=[
                "artist-credits",
                "artist-rels",
                "isrcs",
                "labels",
                "recordings",
                "recording-level-rels",
                "release-groups",
                "tags",
                "work-rels",
                "work-level-rels",
            ],
        )["release"]
        release_group = release["release-group"]
        medium = release["medium-list"][int(self._search_data.disc_number) - 1]
        self._pprint("RELEASE", release)

        artist_id = release["artist-credit"][0]["artist"]["id"]
        artist, _, self.artist_sort_name, self.mb_artist_ids = self._process_artist_credit(
            release["artist-credit"]
        )
        self.artist = release.get("artist-credit-phrase") or artist
        self.album = release["title"].replace("’", "'")
        self.genre = self._get_genre(release_group["id"], artist_id).title()
        self.year = release.get("release-event-list", [{}])[0].get("date") or input(
            "Release year: "
        )
        self.original_date = release_group.get("first-release-date", "")
        self.original_year = self.original_date.split("-")[0] or self.year

        self.tracks = []
        for t in medium["track-list"]:
            r = t["recording"]
            ac = t.get("artist-credit") or r["artist-credit"]
            # It seems that Picard doesn't use the track's artist-relation-list
            # ar = t.get("artist-relation-list") or r["artist-relation-list"] or []
            ar = release.get("artist-relation-list", [])
            track = {
                "number": t["position"],
                "title": (t.get("title") or r["title"]).replace("’", "'"),
                "id": t["id"],
                "recording_id": r["id"],
                "isrc": r.get("isrc-list", []),
            }
            (
                track["artist"],
                track["artist_list"],
                track["artist_sort_order"],
                track["artist_ids"],
            ) = self._process_artist_credit(ac)
            track["relationships"] = self._process_relationships(ar)
            self.tracks.append(track)

        if release["cover-art-archive"]["front"] == "true":
            try:
                self.front_cover = musicbrainzngs.get_image_front(release_id, size=500)
            except (
                musicbrainzngs.musicbrainz.NetworkError,
                musicbrainzngs.musicbrainz.ResponseError,
            ) as err:
                print(f"Error getting front cover: {err}")

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
        self.mb_release_group_id = release_group["id"]
        self.mb_release_id = release_id
