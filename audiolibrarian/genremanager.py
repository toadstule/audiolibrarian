import pickle
import webbrowser
from pathlib import Path
from typing import Dict, List

import mutagen
import mutagen.flac
import mutagen.id3
import mutagen.mp4

from audiolibrarian.musicbrains import MusicBrainsSession


class GenreManager:
    def __init__(self, args):
        self._args = args
        self._mb = MusicBrainsSession()
        self._paths = self._get_all_paths()
        self._paths_by_artist = self._get_paths_by_artist()
        _u, _c = self._get_genres_by_artist()
        self._user_genres_by_artist, self._community_genres_by_artist = _u, _c
        if self._args.update:
            self._update_user_artists()
        elif self._args.tag:
            self._update_tags()

    def _update_tags(self) -> None:
        # Set the genre tags for all songs to the user-based genre
        for artist_id, paths in self._paths_by_artist.items():
            genre = self._user_genres_by_artist.get(artist_id)
            if not genre:
                continue
            for path in paths:
                if path.suffix == ".flac":
                    song = mutagen.flac.FLAC(str(path))
                    current_genre = song.tags["genre"][0]
                    if current_genre != genre:
                        song.tags["genre"] = genre
                        song.save()
                        print(f"{path}: {current_genre} --> {genre}")
                elif path.suffix == ".m4a":
                    song = mutagen.mp4.MP4(str(path))
                    current_genre = song.tags["\xa9gen"][0]
                    if current_genre != genre:
                        song.tags["\xa9gen"] = genre
                        song.save()
                        print(f"{path}: {current_genre} --> {genre}")
                elif path.suffix == ".mp3":
                    song = mutagen.File(str(path))
                    current_genre = str(song.tags["TCON"])
                    if current_genre != genre:
                        id3 = mutagen.id3.ID3(str(path))
                        id3.add(mutagen.id3.TCON(encoding=3, text=genre))
                        id3.save()
                        print(f"{path}: {current_genre} --> {genre}")

    def _update_user_artists(self) -> None:
        # Pull up a web page to allow the user to set the genre for all artists that
        # only have community-base genres.
        for artist_id, artist in sorted(
            self._community_genres_by_artist.items(), key=lambda x: x[1]["name"]
        ):
            i = input(f"Continue with {artist['name']} (YES, no, skip)[Y, n, s]: ").lower().strip()
            if i == "n":
                break
            if i != "s":
                webbrowser.open(f"https://musicbrainz.org/artist/{artist_id}/tags")

    def _get_all_paths(self) -> List[Path]:
        # Returns a list of paths (pathlib.Path objects) for all files in the directories
        # specified in the args
        paths = []
        for directory in self._args.directory:
            paths.extend([p for p in list(Path(directory).glob("**/*")) if p.is_file()])
        return paths

    def _get_paths_by_artist(self) -> Dict[str, List[Path]]:
        # Returns a dict mapping Musicbrainz-artist-ID to a list of paths (pathlib.Path objects)
        # representing audio files by that artist.
        artists = {}
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

    def _get_genres_by_artist(self) -> (Dict[str, str], Dict[str, List[Dict]]):
        # Returns two dicts mapping Musicbrainz-artist-ID to:
        # user: a single genre, set in Musicbrainz by this app's user
        # community: a list genre records (dicts) set in Musicbrainz by the community
        #            with "name" and "count" fields
        user, community = {}, {}
        user_modified = False
        cache_file = Path.home() / ".cache" / "audiolibrarian" / "user-genres.pickle"
        if cache_file.exists():
            with cache_file.open(mode="rb") as cf:
                user = pickle.load(cf)
        for artist_id in self._paths_by_artist:
            if artist_id in user:
                # print("Cache hit:", artist_id, user[artist_id])
                continue  # already in the cache
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
            with cache_file.open(mode="wb") as cf:
                pickle.dump(user, cf)
        return user, community
