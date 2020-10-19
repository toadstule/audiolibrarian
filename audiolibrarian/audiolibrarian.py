"""

Useful stuff: https://help.mp3tag.de/main_tags.html
"""
import glob
import os
import pickle
import pprint
import shutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

import mutagen
import mutagen.easyid3
import mutagen.flac
import mutagen.id3
import mutagen.mp3
import mutagen.mp4

from audiolibrarian import text, audiosource, cmd
from audiolibrarian.discogs import DiscogsInfo
from audiolibrarian.musicbrains import MusicBrainsInfo, MusicBrainsSession

TXXX = mutagen.id3.TXXX
UFID = mutagen.id3.UFID


class AudioLibrarian:
    def __init__(self, args):
        self._args = args

        # directories
        self._work_dir = "/var/tmp/audiolibrarian"
        self._flac_dir = os.path.join(self._work_dir, "flac")
        self._m4a_dir = os.path.join(self._work_dir, "m4a")
        self._mp3_dir = os.path.join(self._work_dir, "mp3")
        self._source_dir = os.path.join(self._work_dir, "source")
        self._wav_dir = os.path.join(self._work_dir, "wav")
        self._lock_file = os.path.join(self._work_dir, "workdir.lock")

        d = self._args.disc
        self._disc_number, self._disc_count = d.split("/") if d else ("1", "1")

        if self._args.command == "rip":
            audio_source = audiosource.CDAudioSource()
        elif self._args.command == "convert":
            audio_source = audiosource.FilesAudioSource(self._args.filename)
        else:
            raise Exception(f"Invalid command: {self._args.command}")

        search_data = audio_source.get_search_data()
        search_data.disc_number = self._disc_number
        if self._args.artist:
            search_data.artist = self._args.artist
        if self._args.album:
            search_data.album = self._args.album
        if self._args.mb_artist_id:
            search_data.mb_artist_id = self._args.mb_artist_id
        if self._args.mb_release_id:
            search_data.mb_release_id = self._args.mb_release_id
        print("DATA:", search_data)
        pprint.pp([os.path.basename(f) for f in audio_source.get_source_filenames()])
        if args.db == "discogs":
            self._info = DiscogsInfo(search_data, args.verbose)
        else:
            self._info = MusicBrainsInfo(search_data, args.verbose)
        pprint.pp(self._info)
        source_filenames = audio_source.get_source_filenames()
        if len(source_filenames) != len(self._info.tracks):
            print("\n*** Track count does not match file count ***\n")
        if input("Confirm [Y,n]: ").lower() == "n":
            return
        audio_source.prepare_source()
        self._acquire_lock()
        try:
            self._make_clean_workdirs()
            audio_source.copy_wavs(self._wav_dir)
            self._rename_wav()
            self._make_source()
            self._normalize()
            self._make_flac()
            self._make_m4a()
            self._make_mp3()
            self._move_files()
        finally:
            self._release_lock()

    @property
    def _flac_filenames(self):
        return sorted(glob.glob(os.path.join(self._flac_dir, "*.flac")))

    @property
    def _m4a_filenames(self):
        return sorted(glob.glob(os.path.join(self._m4a_dir, "*.m4a")))

    @property
    def _mp3_filenames(self):
        return sorted(glob.glob(os.path.join(self._mp3_dir, "*.mp3")))

    @property
    def _source_filenames(self):
        return sorted(glob.glob(os.path.join(self._source_dir, "*.flac")))

    @property
    def _wav_filenames(self):
        return sorted(glob.glob(os.path.join(self._wav_dir, "*.wav")))

    def _acquire_lock(self):
        try:
            while os.path.exists(self._lock_file):
                print("Waiting for lock...")
                time.sleep(5)
        except KeyboardInterrupt:
            if input("Lock not acquired; continue anyway? [N,y] ").lower() != "y":
                sys.exit()
        with open(self._lock_file, "w") as lock_file:
            lock_file.write(str(os.getpid()))

    def _get_artist_album(self):
        if self._args.artist and self._args.album:
            artist, album = None, None
        else:
            artist, album = self._get_artist_album_from_tags()
        artist = self._args.artist or artist
        album = self._args.album or album
        return artist, album

    def _get_artist_album_from_tags(self):
        for filename in self._args.filename:
            album, artist = None, None
            song = mutagen.File(filename)
            pprint.pp(song.tags)
            artist = (
                artist
                or song.tags.get("ALBUMARTIST", [None])[0]
                or song.tags.get("ARTIST", [None])[0]
            )
            album = album or song.tags.get("ALBUM", [None])[0]
            print("Artist from tags:", artist)
            print("Album from tags:", album)
            if artist and album:
                return artist, album
        return None, None

    def _make_clean_workdirs(self):
        if os.path.isdir(self._work_dir):
            shutil.rmtree(self._work_dir)
        for d in self._flac_dir, self._m4a_dir, self._mp3_dir, self._source_dir, self._wav_dir:
            os.makedirs(d)

    def _make_flac(self, source=False):
        out_dir = self._source_dir if source else self._flac_dir
        commands = [
            ("flac", "--silent", f"--output-prefix={out_dir}/", f)
            for f in self._wav_filenames
        ]
        cmd.parallel("Making flac files...", commands, out_dir)
        info = self._info
        shared_tags = {
            "album": [info.album],
            "media": [info.media],
            "label": info.organization,
            "albumartist": [info.artist],
            "albumartistsort": [info.artist_sort_name],
            "date": [str(info.year)],
            "genre": [info.genre],
            "description": [info.get_comment_string()],
            "discnumber": [info.disc_number],
            "disctotal": [self._disc_count],
            "totaldiscs": [self._disc_count],
            "script": ["Latn"],
            "asin": [info.asin],
            "originalyear": [info.original_year],
            "originaldate": [info.original_date],
            "barcode": [info.barcode],
            "catalognumber": [info.catalog_number],
            "releasetype": info.album_type,
            "releasestatus": [info.album_status],
            "releasecountry": [info.country],
            "musicbrainz_albumid": [info.mb_release_id],
            "musicbrainz_albumartistid": [info.mb_artist_id],
            "musicbrainz_releasegroupid": [info.mb_release_group_id],
        }
        for flac in self._source_filenames if source else self._flac_filenames:
            number = str(int(os.path.basename(flac).split("__")[0]))
            song = mutagen.flac.FLAC(flac)
            track = info.get_track(number)
            song.delete()
            song.clear_pictures()
            tags = {
                "artists": track["artist_list"],
                "musicbrainz_releasetrackid": [track["id"]],
                "musicbrainz_trackid": [track["recording_id"]],
                "isrc": track["isrc"],
                "musicbrainz_artistid": track["artist_id"],
                "title": [track["title"]],
                "tracknumber": [str(track["number"])],
                "artist": [track["artist"]],
                "artistsort": [track["artist_sort_order"]],
                "totaltracks": [str(len(info.tracks))],
                "tracktotal": [str(len(info.tracks))],
            }
            song.update(shared_tags)
            song.update(tags)
            if info.front_cover:
                cover = mutagen.flac.Picture()
                cover.type = 3
                cover.mime = "image/jpeg"
                cover.desc = "front cover"
                cover.data = info.front_cover
                song.add_picture(cover)
            song.save()

    def _make_m4a(self):
        commands = []
        for f in self._wav_filenames:
            dst_file = os.path.join(self._m4a_dir, os.path.basename(f).replace(".wav", ".m4a"))
            commands.append(("fdkaac", "--silent", "--bitrate-mode=5", "-o", dst_file, f))
        cmd.parallel("Making m4a files...", commands, self._m4a_dir)
        info = self._info  # we use this a lot below
        disc_x_of_y = (int(info.disc_number), int(self._disc_count))
        shared_tags = {
            "\xa9alb": [info.album],
            "----:com.apple.iTunes:MEDIA": [bytes(info.media, "utf8")],
            "----:com.apple.iTunes:LABEL": [bytes(x, "utf8") for x in info.organization],
            "aART": [info.artist],
            "soaa": [info.artist_sort_name],
            "\xa9day": [str(info.year)],
            "\xa9gen": [info.genre],
            "\xa9cmt": [info.get_comment_string()],
            "disk": [disc_x_of_y],
            "----:com.apple.iTunes:SCRIPT": [bytes("Latn", "utf8")],
            "----:com.apple.iTunes:ASIN": [bytes(info.asin, "utf8")],
            "----:com.apple.iTunes:originalyear": [bytes(info.original_year, "utf8")],
            "----:com.apple.iTunes:originaldate": [bytes(info.original_date, "utf8")],
            "----:com.apple.iTunes:BARCODE": [bytes(info.barcode, "utf8")],
            "----:com.apple.iTunes:CATALOGNUMBER": [bytes(info.catalog_number, "utf8")],
            "----:com.apple.iTunes:MusicBrainz Album Type": [
                bytes(x, "utf8") for x in info.album_type
            ],
            "----:com.apple.iTunes:MusicBrainz Album Status": [bytes(info.album_status, "utf8")],
            "----:com.apple.iTunes:MusicBrainz Album Release Country": [
                bytes(info.country, "utf8")
            ],
            "----:com.apple.iTunes:MusicBrainz Album Id": [bytes(info.mb_release_id, "utf8")],
            "----:com.apple.iTunes:MusicBrainz Album Artist Id": [
                bytes(info.mb_artist_id, "utf8")
            ],
            "----:com.apple.iTunes:MusicBrainz Release Group Id": [
                bytes(info.mb_release_group_id, "utf8")
            ],
        }
        for m4a in self._m4a_filenames:
            number = str(int(os.path.basename(m4a).split("__")[0]))
            song = mutagen.mp4.MP4(m4a)
            track = info.get_track(number)
            song.delete()
            tags = {
                "----:com.apple.iTunes:ARTISTS": [bytes(x, "utf8") for x in track["artist_list"]],
                "----:com.apple.iTunes:MusicBrainz Release Track Id": [bytes(track["id"], "utf8")],
                "----:com.apple.iTunes:MusicBrainz Track Id": [
                    bytes(track["recording_id"], "utf8")
                ],
                "----:com.apple.iTunes:ISRC": [bytes(x, "utf8") for x in track["isrc"]],
                "----:com.apple.iTunes:MusicBrainz Artist Id": [
                    bytes(x, "utf8") for x in track["artist_id"]
                ],
                "\xa9nam": [track["title"]],
                "trkn": [(int(track["number"]), len(info.tracks))],
                "\xa9ART": [track["artist"]],
                "soar": [track["artist_sort_order"]],
            }
            for k, v in shared_tags.items():
                song[k] = v
            for k, v in tags.items():
                song[k] = v
            if info.front_cover:
                cover = mutagen.mp4.MP4Cover(info.front_cover)
                song["covr"] = [cover]
            song.save()

    def _make_mp3(self):
        commands = []
        for f in self._wav_filenames:
            dst_file = os.path.join(self._mp3_dir, os.path.basename(f).replace(".wav", ".mp3"))
            commands.append(("lame", "--silent", "-h", "-b", "192", f, dst_file))
        cmd.parallel("Making mp3 files...", commands, self._mp3_dir)
        info = self._info  # we use this a lot below
        disc_x_of_y = f"{info.disc_number}/{self._disc_count}"
        shared_tags = [
            mutagen.id3.TALB(encoding=3, text=info.album),
            mutagen.id3.TMED(encoding=3, text=info.media),
            mutagen.id3.TPUB(encoding=3, text="/".join(info.organization)),
            mutagen.id3.TPE2(encoding=3, text=info.artist),
            mutagen.id3.TSO2(encoding=3, text=info.artist_sort_name),
            mutagen.id3.TDRC(encoding=3, text=info.year),
            mutagen.id3.TDOR(encoding=3, text=info.original_year),
            mutagen.id3.TCON(encoding=3, text=info.genre),
            mutagen.id3.COMM(encoding=3, text=info.get_comment_string()),
            mutagen.id3.TPOS(encoding=3, text=disc_x_of_y),
            TXXX(encoding=3, desc="SCRIPT", text="Latn"),
            TXXX(encoding=3, desc="ASIN", text=info.asin),
            TXXX(encoding=3, desc="originalyear", text=info.original_year),
            TXXX(encoding=3, desc="BARCODE", text=info.barcode),
            TXXX(encoding=3, desc="CATALOGNUMBER", text=info.catalog_number),
            TXXX(encoding=3, desc="MusicBrainz Album Type", text="/".join(info.album_type)),
            TXXX(encoding=3, desc="MusicBrainz Album Status", text=info.album_status),
            TXXX(encoding=3, desc="MusicBrainz Album Release Country", text=info.country),
            TXXX(encoding=3, desc="MusicBrainz Album Id", text=info.mb_release_id),
            TXXX(encoding=3, desc="MusicBrainz Album Artist Id", text=info.mb_artist_id),
            TXXX(encoding=3, desc="MusicBrainz Release Group Id", text=info.mb_release_group_id),
        ]
        for mp3 in self._mp3_filenames:
            number = str(int(os.path.basename(mp3).split("__")[0]))
            try:
                song = mutagen.id3.ID3(mp3)
            except mutagen.id3.ID3NoHeaderError:
                s = mutagen.File(mp3, easy=False)
                s.add_tags()
                s.save()
                song = mutagen.id3.ID3(mp3)
            track = info.get_track(number)
            song.delete()
            track_x_of_y = f"{track['number']}/{len(info.tracks)}"
            tags = [
                mutagen.id3.TPE1(encoding=3, text=track["artist"]),
                mutagen.id3.TSOP(encoding=3, text=track["artist_sort_order"]),
                mutagen.id3.TIT2(encoding=3, text=track["title"]),
                mutagen.id3.TRCK(encoding=3, text=track_x_of_y),
                mutagen.id3.TSRC(encoding=3, text="/".join(track["isrc"])),
                UFID(owner="http://musicbrainz.org", data=bytes(track["recording_id"], "utf8")),
                TXXX(encoding=3, desc="MusicBrainz Release Track Id", text=track["id"]),
                TXXX(encoding=3, desc="MusicBrainz Artist Id", text="/".join(track["artist_id"])),
                TXXX(encoding=3, desc="ARTISTS", text=track["artist_names"]),
            ]
            for tag in shared_tags + tags:
                song.add(tag)
            if info.front_cover:
                song["APIC"] = mutagen.id3.APIC(
                    encoding=3,
                    mime="image/jpeg",
                    type=3,
                    desc="front cover",
                    data=info.front_cover,
                )
            song.save()

    def _make_source(self):
        self._make_flac(source=True)

    def _move_files(self):
        artist_dir = text.get_filename(self._info.artist)
        album_dir = text.get_filename(f"{self._info.original_year}__{self._info.album}")
        flac_dir = f"library/flac/{artist_dir}/{album_dir}"
        m4a_dir = f"library/m4a/{artist_dir}/{album_dir}"
        mp3_dir = f"library/mp3/{artist_dir}/{album_dir}"
        source_dir = f"library/source/{artist_dir}/{album_dir}"
        if self._args.disc:
            flac_dir += f"/disc{self._disc_number}"
            m4a_dir += f"/disc{self._disc_number}"
            mp3_dir += f"/disc{self._disc_number}"
            source_dir += f"/disc{self._disc_number}"
        for d in (flac_dir, m4a_dir, mp3_dir, source_dir):
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d)
        [os.rename(f, f"{flac_dir}/{os.path.basename(f)}") for f in self._flac_filenames]
        [os.rename(f, f"{m4a_dir}/{os.path.basename(f)}") for f in self._m4a_filenames]
        [os.rename(f, f"{mp3_dir}/{os.path.basename(f)}") for f in self._mp3_filenames]
        [os.rename(f, f"{source_dir}/{os.path.basename(f)}") for f in self._source_filenames]

    def _normalize(self):
        print("Normalizing wav files...")
        # command = ["wavegain", "--album", "--apply"]
        command = ["wavegain", "--radio", "--gain=5", "--apply"]
        command.extend(glob.glob(self._wav_dir))
        r = subprocess.run(command, stdout=subprocess.DEVNULL)
        r.check_returncode()

    def _release_lock(self):
        if os.path.exists(self._lock_file):
            os.remove(self._lock_file)

    def _rename_wav(self):
        number = 0
        for filename in self._wav_filenames:
            number += 1
            path, base = os.path.split(filename)
            track = self._info.get_track(str(number))
            new_name = os.path.join(path, f"{track['filename']}.wav")
            if new_name != filename:
                print(f"{os.path.basename(filename)} --> {os.path.basename(new_name)}")
                os.rename(filename, new_name)


class GenreManager:
    def __init__(self, args):
        self._args = args
        self._mb = MusicBrainsSession()
        self._paths = self._get_all_paths()
        self._paths_by_artist = self._get_paths_by_artist()
        _u, _c = self._get_genres_by_artist()
        self._user_genres_by_artist, self._community_genres_by_artist = _u, _c
        if self._args.update:
            self._update_community_artists()
        elif self._args.tag:
            self._update_tags()

    def _update_tags(self):
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

    def _update_community_artists(self):
        for artist_id, artist in sorted(
            self._community_genres_by_artist.items(), key=lambda x: x[1]["name"]
        ):
            i = input(f"Continue with {artist['name']} [Y, n, s]: ").lower().strip()
            if i == "n":
                break
            if i != "s":
                webbrowser.open(f"https://musicbrainz.org/artist/{artist_id}/tags")

    def _get_all_paths(self):
        paths = []
        for directory in self._args.directory:
            paths.extend([p for p in list(Path(directory).glob("**/*")) if p.is_file()])
        return paths

    def _get_paths_by_artist(self):
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

    def _get_genres_by_artist(self):
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
