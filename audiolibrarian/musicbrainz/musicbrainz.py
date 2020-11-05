import pprint
import time
from typing import Dict, List, Tuple

import musicbrainzngs as mb
import requests
from requests.auth import HTTPDigestAuth

from audiolibrarian import __version__
from audiolibrarian.records import People, Performer, Release, Track
from audiolibrarian.records.records import Medium, Source
from audiolibrarian.text import fix

mb.set_useragent("audiolibrarian", __version__, "steve@jibson.com")


class MusicBrainsSession:
    def __init__(self):
        self._session = requests.Session()
        self._session.auth = HTTPDigestAuth("toadstule", "***REMOVED***")
        self._session.headers.update(
            {"User-Agent": f"audiolibrarian/{__version__}/steve@jibson.com"}
        )

    def __del__(self):
        self._session.close()

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


class MusicBrainzRelease:
    _includes = [
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
    ]

    def __init__(self, release_id: str, verbose: bool = False):
        self._release_id = release_id
        self._verbose = verbose
        self._session = MusicBrainsSession()
        self._release = mb.get_release_by_id(release_id, includes=self._includes)["release"]
        self._release_record = None

    def get_release(self) -> Release:
        if self._release_record is None:
            self._release_record = self._get_release()
        return self._release_record

    # def get_one_track(self, track_number: int = 1) -> OneTrack:
    #     release_view = self.get_release_view()
    #     for track in release_view.tracks:
    #         if track.track_number == track_number:
    #             break
    #     else:
    #         track = None
    #     return OneTrack(release=release_view.release, track=track)

    def _get_front_cover(self, size: int = 500):
        if self._release["cover-art-archive"]["front"] == "true":
            try:
                return mb.get_image_front(self._release["id"], size=size)
            except (
                mb.musicbrainz.NetworkError,
                mb.musicbrainz.ResponseError,
            ) as err:
                print(f"Error getting front cover: {err}")

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

    def _get_media(self) -> (Dict[int, Medium], None):
        media = {}
        for medium in self._release.get("medium-list", []):
            medium_number = int(medium.get("number") or medium.get("position"))
            media[medium_number] = Medium(
                format=[medium["format"]],
                track_count=medium["track-count"],
                tracks=self._get_tracks(medium_number=medium_number),
            )
        return media

    def _get_people(self) -> (People, None):
        engineers, lyricists, mixers, performers, producers = [], [], [], [], []
        for r in self._release.get("artist-relation-list", []):
            name = fix(r["artist"]["name"])
            type_ = r["type"].lower()
            if type_ == "engineer":
                engineers.append(name)
            elif type_ == "lyricist":
                lyricists.append(name)
            elif type_ == "mix":
                mixers.append(name)
            elif type_ == "instrument":
                performers.append(
                    Performer(name=name, instrument=fix(",".join(r["attribute-list"])))
                )
            elif type_ == "vocal":
                performers.append(Performer(name=name, instrument="lead vocals"))
            elif type_ == "producer":
                producers.append(name)
            else:
                print(f"Unknown artist-relation type: {type_}")
        if engineers or lyricists or mixers or performers or producers:
            return People(
                engineers=engineers or None,
                lyricists=lyricists or None,
                mixers=mixers or None,
                performers=performers or None,
                producers=producers or None,
            )

    def _get_release(self) -> Release:
        release = self._release
        self._pprint("RELEASE", release)
        release_group = release["release-group"]
        (
            album_artist_names_str,
            _,
            album_artist_sort_names,
            artist_ids,
        ) = self._process_artist_credit(release["artist-credit"])
        artist_phrase = fix(release.get("artist-credit-phrase", ""))
        year = release.get("release-event-list", [{}])[0].get("date") or input("Release year: ")
        album_type = [release_group["primary-type"].lower()]
        if release_group["type"].lower() != album_type[0]:
            album_type.append(release_group["type"].lower())

        labels = list(dict.fromkeys([x["label"]["name"] for x in release["label-info-list"]]))

        key = "catalog-number"
        catalog_numbers = list(
            dict.fromkeys([x[key] for x in release.get("label-info-list", []) if x.get(key)])
        )
        return Release(
            album=fix(release["title"]),
            album_artists=[artist_phrase or album_artist_names_str],
            album_artists_sort=[album_artist_sort_names],
            asins=[release["asin"]] if release.get("asin") else None,
            barcodes=[release["barcode"]] if release.get("barcode") else None,
            catalog_numbers=catalog_numbers or None,
            date=year,
            front_cover=self._get_front_cover(),
            genres=[self._get_genre(release_group["id"], artist_ids[0]).title()],
            labels=labels,
            media=self._get_media(),
            medium_count=release.get("medium-count", 0),
            musicbrainz_album_artist_ids=artist_ids,
            musicbrainz_album_id=self._release_id,
            musicbrainz_release_group_id=release_group["id"],
            original_date=release_group.get("first-release-date", ""),
            original_year=release_group.get("first-release-date", "").split("-")[0] or year,
            people=self._get_people(),
            release_countries=[release.get("country", "")],
            release_statuses=[release.get("status", "").lower()],
            release_types=album_type,
            script="Latn",
            source=Source.MUSICBRAINZ,
        )

    def _get_tracks(self, medium_number: int = 1) -> (Dict[int, Track], None):
        tracks = {}
        for medium in self._release.get("medium-list", []):
            if int(medium["position"]) == medium_number:
                for t in medium["track-list"]:
                    track_number = int(t["number"])
                    recording = t["recording"]
                    artist, artist_list, artist_sort, artist_ids = self._process_artist_credit(
                        t.get("artist-credit") or recording["artist-credit"]
                    )
                    tracks[track_number] = Track(
                        artist=artist,
                        artists=artist_list,
                        artists_sort=[artist_sort],
                        isrcs=recording.get("isrc-list"),
                        musicbrainz_artist_ids=artist_ids,
                        musicbrainz_release_track_id=t["id"],
                        musicbrainz_track_id=recording["id"],
                        title=fix(t.get("title") or recording["title"]),
                        track_number=track_number,
                    )
                break
        return tracks or None

    def _pprint(self, name, obj, indent=0):
        if self._verbose:
            print(name, "-" * (78 - len(name)))
            pprint.pp(obj, indent=indent)
            print("-" * 79)

    @staticmethod
    def _process_artist_credit(artist_credit: list) -> Tuple[str, List[str], str, List[str]]:
        # Get artist info from an artist-credit
        artist_names_str = ""
        artist_names_list = []
        artist_sort_names = ""
        artist_ids = []
        for a in artist_credit:
            if isinstance(a, dict):
                artist_names_str += fix(a.get("name") or a["artist"]["name"])
                artist_names_list.append(fix(a.get("name") or a["artist"]["name"]))
                artist_sort_names += fix(a["artist"]["sort-name"])
                artist_ids.append(fix(a["artist"]["id"]))
            else:
                artist_names_str += fix(a)
                artist_sort_names += fix(a)
        return artist_names_str, artist_names_list, artist_sort_names, artist_ids

    @staticmethod
    def _process_relationships(relationships: list) -> List[Tuple[str, str]]:
        result = []
        for r in relationships:
            value = r["artist"]["name"]
            type_ = r["type"].lower()
            if type_ == "instrument":
                key = "PERFORMER"
                value = f"{r['artist']['name']} ({','.join(r['attribute-list'])})"
            elif type_ == "mix":
                key = "MIXER"
            elif type_ == "vocal":
                key = "PERFORMER"
                value = f"{r['artist']['name']} (lead vocals)"
            else:
                key = r["type"].upper()
            result.append((key, fix(value)))
        return result
