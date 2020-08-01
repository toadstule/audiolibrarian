import requests
from fuzzywuzzy import fuzz

from audiolibrarian.audioinfo import AudioInfo
from audiolibrarian.output import Dots

"""
"This application uses Discogs’ API but is not affiliated with, sponsored or endorsed by Discogs.
‘Discogs’ is a trademark of Zink Media, LLC."
"""

key = "SQopyYBLoKcfmoAPbnKg"
secret = "NlcgnWwAiTrNAiZYHUtWXiicxUxHRFOj"


class DiscogsInfo(AudioInfo):
    def __init__(self, artist, album, disc_number, verbose=False):

        # Deprecated (and maybe will stay that way forever?)
        _, _, _, _ = artist, album, disc_number, verbose
        raise DeprecationWarning("Discogs is not currently supported")

        # noinspection PyUnreachableCode
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "jib-audio/0.1",
                "Authorization": f"Discogs key={key}, secret={secret}",
            }
        )
        super().__init__(artist, album, disc_number, verbose)

    def _get(self, path, params=None):
        path = path.lstrip("/")
        url = f"https://api.discogs.com/{path}"
        r = self._session.get(url, params=params)
        assert r.status_code == 200, f"{r.status_code} - {url}"
        return r.json()

    def _get_artist_id(self):
        artist = self._input_artist
        album = self._input_album
        url = f"database/search"
        params = {"q": artist, "type": "artist", "title": album, "per_page": 100}
        j = self._get(url, params)
        if not j.get("results"):  # search without album title
            del params["title"]
            j = self._get(url, params)
        try:
            return j["results"][0]["id"]
        except KeyError:
            raise Exception(f"Artist not found: {artist}")

    def _get_release_ids(self, artist_id):
        all_releases = []
        album_l = self._input_album.lower()
        page = 0
        with Dots("Getting releases") as dots:
            while True:
                dots.dot()
                page += 1
                url = f"artists/{artist_id}/releases"
                params = {"per_page": 100, "page": page}
                j = self._get(url, params)
                all_releases.extend(j["releases"])
                pages = int(j.get("pagination", {}).get("pages", "1"))
                if page >= pages:
                    break
        self._pprint("ALL_RELEASES", all_releases)
        releases = [r for r in all_releases if fuzz.ratio(r["title"].lower(), album_l) > 80]
        masters = [r for r in releases if r.get("type") == "master" and r.get("role") == "Main"]
        self._pprint("MASTERS", masters)
        return [m["id"] for m in masters]

    def _prompt_release_id(self, master_ids, artist_id):
        if master_ids:
            print(
                "\n\nWe found the following master release(s). Use the link(s) below to "
                "find the release ID that best matches the audio files.\n"
            )
            for master_id in master_ids:
                master_info = self._get(f"masters/{master_id}")
                print(f"{master_info['uri']}?filter=true")
        else:
            print("\n\nWe found the following artist. Use the links below to ")
            print("find the release ID that best matches the audio files.\n")
            artist_info = self._get(f"artists/{artist_id}")
            print(f"{artist_info['uri']}")

        while True:
            release_input = input("\nRelease ID or URL: ")
            try:
                release_id = int(release_input.split("/")[-1])
            except ValueError:
                pass
            else:
                return release_id

    def _update(self):
        artist_id = self._get_artist_id()
        print("ARTIST_ID:", artist_id)
        master_release_ids = self._get_release_ids(artist_id)
        release_id = self._prompt_release_id(master_release_ids, artist_id)
        print("RELEASE_ID:", release_id)
        release = self._get(f"releases/{release_id}")
        self._pprint("RELEASE", release)

        if "master_id" in release:
            master_info = self._get(f"masters/{release['master_id']}")
            main_release = self._get(f"releases/{master_info['main_release']}")
            self._pprint("MAIN_RELEASE", main_release)
            self.year = master_info["year"]
        else:
            master_info, main_release = None, None
            self.year = release["year"]

        self.artist = release["artists"][0]["name"]
        self.artist_sort_name = release["artists_sort"]
        self.album = release["title"]
        self.genre = release["genres"][0] if "genres" in release else ""

        if "images" in release:
            images_ = release["images"]
        elif main_release and "images" in main_release:
            images_ = main_release["images"]
        else:
            images_ = None

        if images_:
            images = [i["uri"] for i in images_ if i["type"] == "primary"] or [
                i["uri"] for i in images_ if i["type"] == "secondary"
            ]
            self.front_cover = self._get_image(url=images[0])

        self.tracks = [
            {"number": t["position"].zfill(2), "title": t["title"]} for t in release["tracklist"]
        ]

        if master_info and release["year"] != master_info["year"]:
            self.comments.append(f"Year: {release['year']}")

    def _get_image(self, url):
        image_data = b""
        r = self._session.get(url, stream=True)
        assert r.status_code == 200
        for chunk in r:
            image_data += chunk
        return image_data
