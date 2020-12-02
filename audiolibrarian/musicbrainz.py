#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

import pprint
import time
import webbrowser
from dataclasses import dataclass
from datetime import datetime, timedelta
from logging import DEBUG, getLogger

import musicbrainzngs as mb
import requests
from fuzzywuzzy import fuzz
from requests.auth import HTTPDigestAuth

from audiolibrarian import __version__
from audiolibrarian.records import (
    FrontCover,
    ListF,
    Medium,
    People,
    Performer,
    Release,
    Source,
    Track,
)
from audiolibrarian.text import fix, get_uuid, input_, join

log = getLogger(__name__)
_user_agent_name = "audiolibrarian"
_user_agent_contact = "audiolibrarian@jibson.com"
mb.set_useragent(_user_agent_name, __version__, _user_agent_contact)


class MusicBrainzSession:
    """MusicBrainzSession provides access to the MusicBrainz API.

    It can be for things that are not supported by the musicbrainzngs library.
    """

    _api_rate = timedelta(seconds=1.5)
    _last_api_call = datetime.now()

    def __init__(self):
        self.__session = None

    def __del__(self):
        if self.__session is not None:
            self.__session.close()

    @property
    def _session(self):
        if self.__session is None:
            self.__session = requests.Session()
            self._session.auth = HTTPDigestAuth("toadstule", "***REMOVED***")
            self._session.headers.update(
                {"User-Agent": f"{_user_agent_name}/{__version__} ({_user_agent_contact})"}
            )
        return self.__session

    def _get(self, path: str, params=None):
        # Used for direct API calls; those not supported by the python library
        path = path.lstrip("/")
        url = f"https://musicbrainz.org/ws/2/{path}"
        params["fmt"] = "json"
        self.sleep()
        r = self._session.get(url, params=params)
        while r.status_code == 503:
            log.warning("Waiting due to throttling...")
            time.sleep(10)
            r = self._session.get(url, params=params)
        assert r.status_code == 200, f"{r.status_code} - {url}"
        return r.json()

    def get_artist_by_id(self, artist_id: str, includes=None):
        """Returns artist for the given musicbrainz-artist ID."""
        params = {}
        if includes is not None:
            params["inc"] = "+".join(includes)
        return self._get(f"artist/{artist_id}", params=params)

    def get_release_group_by_id(self, release_group_id: str, includes=None):
        """Returns release-group for the given musicbrainz-release-group ID."""
        params = {}
        if includes is not None:
            params["inc"] = "+".join(includes)
        return self._get(f"release-group/{release_group_id}", params=params)

    @staticmethod
    def sleep():
        """Sleep so we don't abuse the MusicBrainz API service.

        See https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting
        """
        since_last = datetime.now() - MusicBrainzSession._last_api_call
        if (sleep_seconds := (MusicBrainzSession._api_rate - since_last).total_seconds()) > 0:
            log.debug(f"Sleeping {sleep_seconds} to avoid throttling...")
            time.sleep(sleep_seconds)
            MusicBrainzSession._last_api_call = datetime.now()


class MusicBrainzRelease:
    """MusicBrainzRelease reads information from MusicBrains and provides a Release record."""

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
        self._session = MusicBrainzSession()
        self._session.sleep()
        self._release = mb.get_release_by_id(release_id, includes=self._includes)["release"]
        self._release_record = None

    def get_release(self) -> Release:
        """Returns the Release record."""
        if self._release_record is None:
            self._release_record = self._get_release()
        return self._release_record

    def _get_front_cover(self, size: int = 500) -> (FrontCover, None):
        # Returns the FrontCover object (of None).
        if self._release["cover-art-archive"]["front"] == "true":
            self._session.sleep()
            try:
                return FrontCover(
                    data=mb.get_image_front(self._release["id"], size=size),
                    desc="front",
                    mime="image/jpeg",
                )
            except (
                mb.musicbrainz.NetworkError,
                mb.musicbrainz.ResponseError,
            ) as err:
                log.warning(f"Error getting front cover: {err}")

    def _get_genre(self, release_group_id: str, artist_id: str) -> str:
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
        log.info(f"RELEASE_GROUP_GENRES: {rg}")
        at = self._session.get_artist_by_id(artist_id, includes=["genres", "user-genres"])
        log.info(f"ARTIST_GENRES: {at}")
        if rg["user-genres"]:
            return rg["user-genres"][0]["name"]
        if at["user-genres"]:
            return at["user-genres"][0]["name"]
        if rg["genres"]:
            return [g["name"] for g in reversed(sorted(rg["genres"], key=lambda x: x["count"]))][0]
        if at["genres"]:
            return [g["name"] for g in reversed(sorted(at["genres"], key=lambda x: x["count"]))][0]
        return input_("Genre not found; enter the genre [Alternative]: ") or "Alternative"

    def _get_media(self) -> (dict[int, Medium], None):
        # Returns a dict of Media objects, keyed on number or position (or None).
        media = {}
        for medium in self._release.get("medium-list", []):
            medium_number = int(medium.get("number") or medium.get("position"))
            media[medium_number] = Medium(
                formats=ListF([medium["format"]]),
                titles=[fix(medium["title"])] if medium.get("title") else None,
                track_count=medium["track-count"],
                tracks=self._get_tracks(medium_number=medium_number),
            )
        return media

    def _get_people(self) -> (People, None):
        # Returns a People object (or None).
        arrangers, composers, conductors, engineers, lyricists = [], [], [], [], []
        mixers, performers, producers, writers = [], [], [], []
        for r in self._release.get("artist-relation-list", []):
            if log.getEffectiveLevel() == DEBUG:
                pprint.pp("== ARTIST-RELATION-LIST ===================")
                pprint.pp(r)
            name = fix(r["artist"]["name"])
            type_ = r["type"].lower()
            if type_ == "arranger":
                arrangers.append(name)
            elif type_ == "composer":
                composers.append(name)
            elif type_ == "conductor":
                conductors.append(name)
            elif type_ == "engineer":
                engineers.append(name)
            elif type_ == "lyricist":
                lyricists.append(name)
            elif type_ == "mix":
                mixers.append(name)
            elif type_ == "instrument":
                performers.append(Performer(name=name, instrument=fix(join(r["attribute-list"]))))
            elif type_ == "vocal":
                performers.append(Performer(name=name, instrument="lead vocals"))
                if attrs := r.get("attribute-list"):
                    if attrs := [x for x in attrs if x != "lead vocals"]:
                        performers.append(Performer(name=name, instrument=fix(join(attrs))))
                else:
                    performers.append(Performer(name=name, instrument="vocals"))
            elif type_ == "producer":
                producers.append(name)
            elif type_ == "writer":
                writers.append(name)
            else:
                log.warning(f"Unknown artist-relation type: {type_}")
        if (
            engineers
            or arrangers
            or composers
            or conductors
            or lyricists
            or mixers
            or performers
            or producers
            or writers
        ):
            return People(
                arrangers=arrangers or None,
                composers=composers or None,
                conductors=conductors or None,
                engineers=engineers or None,
                lyricists=lyricists or None,
                mixers=mixers or None,
                performers=performers or None,
                producers=producers or None,
                writers=writers or None,
            )

    def _get_release(self) -> Release:
        # Returns the Release object.
        release = self._release
        log.info(f"RELEASE {release}")
        if log.getEffectiveLevel() == DEBUG:
            pprint.pp("== RELEASE ===================")
            pprint.pp(release)
        release_group = release["release-group"]
        (
            album_artist_names_str,
            _,
            album_artist_sort_names,
            artist_ids,
        ) = self._process_artist_credit(release["artist-credit"])
        artist_phrase = fix(release.get("artist-credit-phrase", ""))
        year = release.get("release-event-list", [{}])[0].get("date") or input_("Release year: ")
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
            album_artists=ListF([artist_phrase or album_artist_names_str]),
            album_artists_sort=ListF([album_artist_sort_names]),
            asins=[release["asin"]] if release.get("asin") else None,
            barcodes=[release["barcode"]] if release.get("barcode") else None,
            catalog_numbers=catalog_numbers or None,
            date=year,
            front_cover=self._get_front_cover(),
            genres=ListF([self._get_genre(release_group["id"], artist_ids.first).title()]),
            labels=labels,
            media=self._get_media(),
            medium_count=release.get("medium-count", 0),
            musicbrainz_album_artist_ids=ListF(artist_ids),
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

    def _get_tracks(self, medium_number: int = 1) -> (dict[int, Track], None):
        # Returns a dict of Track objects, keyed on track number.
        tracks = {}
        for medium in self._release.get("medium-list", []):
            if int(medium["position"]) == medium_number:
                for t in medium["track-list"]:
                    track_number = int(t["position"])
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

    @staticmethod
    def _process_artist_credit(artist_credit: list) -> tuple[str, ListF, str, ListF]:
        # Returns artist info from an artist-credit list.
        artist_names_str = ""
        artist_names_list = ListF()
        artist_sort_names = ""
        artist_ids = ListF()
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


@dataclass
class Searcher:
    """Searcher objects contain data and methods for searching the MusicBrainz database."""

    artist: str = ""
    album: str = ""
    disc_id: str = ""
    disc_mcn: str = ""
    disc_number: str = ""
    mb_artist_id: str = ""
    mb_release_id: str = ""
    __mb_session = None

    @property
    def _mb_session(self):
        if self.__mb_session is None:
            self.__mb_session = MusicBrainzSession()
        return self.__mb_session

    def find_music_brains_release(self) -> (Release, None):
        # Returns a Release object (or None) based on a search.
        release_id = self.mb_release_id
        if not release_id and self.disc_id:
            self._mb_session.sleep()
            result = mb.get_releases_by_discid(self.disc_id, includes=["artists"])
            log.info("DISC: {result}")
            if result.get("disc"):
                release_id = result["disc"]["release-list"][0]["id"]
            elif result.get("cdstub"):
                print("A CD Stub exists for this disc, but no disc.")

        if release_id:
            log.info(f"RELEASE: https://musicbrainz.org/release/{release_id}")
        elif self.artist and self.album:
            release_group_ids = self._get_release_group_ids()
            log.info("RELEASE_GROUPS: {release_group_ids}")
            release_id = self._prompt_release_id(release_group_ids)
        else:
            release_id = self._prompt_uuid("Musicbrainz Release ID: ")

        return MusicBrainzRelease(release_id).get_release()

    def _get_release_group_ids(self) -> list[str]:
        # Returns release groups that fuzzy-match the search criteria.
        artist_l = self.artist.lower()
        album_l = self.album.lower()
        self._mb_session.sleep()
        artist_list = mb.search_artists(query=artist_l, limit=500)["artist-list"]
        if not artist_list:
            return []
        artist_id = artist_list[0]["id"]
        self._mb_session.sleep()
        release_group_list = mb.browse_release_groups(artist=artist_id, limit=500)[
            "release-group-list"
        ]
        log.info(f"RELEASE_GROUPS: {release_group_list}")
        if log.getEffectiveLevel() == DEBUG:
            pprint.pp("== RELEASE_GROUPS ===================")
            pprint.pp(release_group_list)
        return [
            rg["id"]
            for rg in release_group_list
            if rg.get("primary-type") == "Album" and fuzz.ratio(album_l, rg["title"].lower()) > 80
        ]

    def _prompt_release_id(self, release_group_ids: list[str]) -> str:
        # Prompt for, and return a MusicBrainz release ID.
        print(
            "\n\nWe found the following release group(s). Use the link(s) below to "
            "find the release ID that best matches the audio files.\n"
        )
        for release_group_id in release_group_ids:
            url = f"https://musicbrainz.org/release-group/{release_group_id}"
            print(url)
            webbrowser.open(url)
        return self._prompt_uuid("\nRelease ID or URL: ")

    @staticmethod
    def _prompt_uuid(prompt: str) -> str:
        # Prompt for, and return a UUID.
        while True:
            uuid = get_uuid(input_(prompt))
            if uuid is not None:
                return uuid
