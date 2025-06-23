"""Genre Manager."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
import argparse
import logging
import pathlib
import pickle
import typing
import webbrowser
from typing import Any

import mutagen
import mutagen.flac
import mutagen.id3
import mutagen.mp4

from audiolibrarian import musicbrainz, text
from audiolibrarian.settings import SETTINGS

log = logging.getLogger(__name__)


class GenreManager:
    """Manage genres."""

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a GenreManager instance."""
        self._args = args
        self._mb = musicbrainz.MusicBrainzSession()
        self._paths = self._get_all_paths()
        self._paths_by_artist = self._get_paths_by_artist()
        _u, _c = self._get_genres_by_artist()
        self._user_genres_by_artist, self._community_genres_by_artist = _u, _c
        if self._args.update:
            self._update_user_artists()
        elif self._args.tag:
            self._update_tags()  # type: ignore[no-untyped-call]

    @typing.no_type_check  # The mutagen library doesn't provide type hints.
    def _update_tags(self) -> None:
        """Set the genre tags for all songs to the user-based genre."""
        for artist_id, paths in self._paths_by_artist.items():
            genre = self._user_genres_by_artist.get(artist_id)
            if not genre:
                continue
            for path in paths:
                if path.suffix == ".flac":
                    flac_song = mutagen.flac.FLAC(str(path))
                    current_genre = flac_song.tags["genre"][0]
                    if current_genre != genre:
                        flac_song.tags["genre"] = genre
                        flac_song.save()
                        print(f"{path}: {current_genre} --> {genre}")
                elif path.suffix == ".m4a":
                    m4a_song = mutagen.mp4.MP4(str(path))
                    current_genre = m4a_song.tags["\xa9gen"][0]
                    if current_genre != genre:
                        m4a_song.tags["\xa9gen"] = genre
                        m4a_song.save()
                        print(f"{path}: {current_genre} --> {genre}")
                elif path.suffix == ".mp3":
                    mp3_song = mutagen.File(str(path))
                    current_genre = str(mp3_song.tags["TCON"])
                    if current_genre != genre:
                        id3 = mutagen.id3.ID3(str(path))
                        id3.add(mutagen.id3.TCON(encoding=3, text=genre))
                        id3.save()
                        print(f"{path}: {current_genre} --> {genre}")

    def _update_user_artists(self) -> None:
        """Pull up a web page to allow the user to set the genre.

        Update the genre for all artists that only have community-base genres.
        """
        for artist_id, artist in sorted(
            self._community_genres_by_artist.items(),
            key=lambda x: x[1]["name"],
        ):
            artist_name = artist["name"]
            i = (
                text.input_(f"Continue with {artist_name} (YES, no, skip)[Y, n, s]: ")
                .lower()
                .strip()
            )
            if i == "n":
                break
            if i != "s":
                webbrowser.open(f"https://musicbrainz.org/artist/{artist_id}/tags")

    def _get_all_paths(self) -> list[pathlib.Path]:
        """Return a list of paths for all files in the directories specified in the args."""
        paths = []
        for directory in self._args.directory:
            paths.extend([p for p in list(pathlib.Path(directory).glob("**/*")) if p.is_file()])
        return paths

    def _get_paths_by_artist(self) -> dict[str, list[pathlib.Path]]:
        """Return a map of artist-IDs to paths representing audio files by that artist."""
        artists: dict[str, list[pathlib.Path]] = {}
        for path in self._paths:
            artist_id = None
            song = mutagen.File(str(path))
            if path.suffix == ".flac":
                artist_id = str(
                    song.tags.get("musicbrainz_albumartistid", [""])[0]
                    or song.tags.get("musicbrainz_artistid", [""])[0]
                )
            elif path.suffix == ".m4a":
                artist_id = (
                    song.tags.get("----:com.apple.iTunes:MusicBrainz Album Artist Id", [""])[0]
                    or song.tags.get("----:com.apple.iTunes:MusicBrainz Artist Id", [""])[0]
                ).decode("utf8")
            elif path.suffix == ".mp3":
                artist_id = str(
                    song.tags.get("TXXX:MusicBrainz Album Artist Id", [""])[0]
                    or song.tags.get("TXXX:MusicBrainz Artist Id", [""])[0]
                )
            if artist_id:
                if artist_id not in artists:
                    artists[artist_id] = []
                artists[artist_id].append(path)
        return artists

    def _get_genres_by_artist(
        self,
    ) -> tuple[dict[str, str], dict[str, dict[str, Any]]]:
        """Return two dicts mapping MusicBrainz-artist-ID to user and community.

        Returns:
          user: a single genre, set in MusicBrainz by this app's user
          community: a list genre records (dicts) set in MusicBrainz by the community
                     with "name" and "count" fields
        """
        user: dict[str, str] = {}
        community: dict[str, dict[str, Any]] = {}
        user_modified = False
        cache_file = SETTINGS.work_dir / "user-genres.pickle"
        if cache_file.exists():
            with cache_file.open(mode="rb") as cache_file_obj:
                user = pickle.load(cache_file_obj)  # noqa: S301
        for artist_id in self._paths_by_artist:
            if artist_id in user:
                log.debug("Cache hit: %s %s", artist_id, user[artist_id])
                continue  # Already in the cache.
            artist = self._mb.get_artist_by_id(artist_id, includes=["genres", "user-genres"])
            if artist["user-genres"]:
                genre = artist["user-genres"][0]["name"].title()
                user[artist_id] = genre
                user_modified = True
            elif artist["genres"]:
                community[artist_id] = {
                    "name": artist["name"],
                    "genres": [{"name": x["name"], "count": x["count"]} for x in artist["genres"]],
                }
        if user_modified:
            cache_file.parent.mkdir(exist_ok=True)
            with cache_file.open(mode="wb") as cache_file_obj:
                # noinspection PyTypeChecker
                pickle.dump(user, cache_file_obj)

        return user, community
