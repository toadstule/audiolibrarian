import glob
import os
import pprint
import shutil
import subprocess

import mutagen
import mutagen.flac
import mutagen.easyid3
import mutagen.id3
import mutagen.mp3
import mutagen.mp4

from audiolibrarian import text
from audiolibrarian.discogs import DiscogsInfo
from audiolibrarian.musicbrains import MusicBrainsInfo
from audiolibrarian.output import Dots


class AudioLibrarian:
    def __init__(self, args):
        self._args = args
        print(self._args)
        self._work_dir = "workdir"
        self._flac_dir = os.path.join(self._work_dir, "flac")
        self._m4a_dir = os.path.join(self._work_dir, "m4a")
        self._mp3_dir = os.path.join(self._work_dir, "mp3")
        self._wav_dir = os.path.join(self._work_dir, "wav")

        artist, album = self._get_artist_album()
        if args.db == "mb":
            self._info = MusicBrainsInfo(artist, album, args.verbose)
        else:
            self._info = DiscogsInfo(artist, album, args.verbose)
        pprint.pp(self._args.files)
        pprint.pp(self._info)
        if input("Confirm [Y,n]: ").lower() == "n":
            return

        self._make_clean_workdirs()
        self._make_wav()
        self._rename_wav()
        self._normalize()
        self._make_flac()
        self._make_m4a()
        self._make_mp3()
        self._move_files()

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
    def _wav_filenames(self):
        return sorted(glob.glob(os.path.join(self._wav_dir, "*.wav")))

    def _get_artist_album(self):
        if self._args.artist and self._args.album:
            artist, album = None, None
        else:
            artist, album = self._get_artist_album_from_tags()
        artist = self._args.album or artist
        album = self._args.album or album
        return artist, album

    def _get_artist_album_from_tags(self):
        for filename in self._args.files:
            album, artist = None, None
            song = mutagen.File(filename)
            print(song.tags)
            artist = (
                artist
                or song.tags.get("ALBUMARTIST", [None])[0]
                or song.tags.get("ARTIST", [None])[0]
            )
            print(artist)
            album = album or song.tags.get("ALBUM", [None])[0]
            print(album)
            if artist and album:
                return artist, album
        return None, None

    def _make_clean_workdirs(self):
        if os.path.isdir(self._work_dir):
            shutil.rmtree(self._work_dir)
        for d in self._flac_dir, self._m4a_dir, self._mp3_dir, self._wav_dir:
            os.makedirs(d)

    def _make_flac(self):
        commands = [
            ("flac", "--silent", f"--output-prefix={self._flac_dir}/", f)
            for f in self._wav_filenames
        ]
        self._parallel("Making flac files...", commands, self._flac_dir)
        for flac in self._flac_filenames:
            number = os.path.basename(flac).split("__")[0]
            song = mutagen.flac.FLAC(flac)
            track = self._info.get_track(number)
            song.delete()
            song.clear_pictures()
            song.update(
                {
                    "ARTIST": self._info.artist,
                    "ALBUMARTIST": self._info.artist,
                    "ARTISTSORT": self._info.artist_sort_name,
                    "ALBUMARTISTSORT": self._info.artist_sort_name,
                    "ALBUM": self._info.album,
                    "DATE": str(self._info.year),
                    "GENRE": self._info.genre,
                    "TITLE": track["title"],
                    "TRACKNUMBER": str(track["number"]),
                    "TRACKTOTAL": str(len(self._info.tracks)),
                    "DESCRIPTION": self._info.get_comment_string(),
                }
            )
            if self._info.front_cover:
                cover = mutagen.flac.Picture()
                cover.type = 3
                cover.mime = "image/jpeg"
                cover.desc = "front cover"
                cover.data = self._info.front_cover
                song.add_picture(cover)
            song.save()

    def _make_m4a(self):
        commands = []
        for f in self._wav_filenames:
            dst_file = os.path.join(self._m4a_dir, os.path.basename(f).replace(".wav", ".m4a"))
            commands.append(("fdkaac", "--silent", "--bitrate-mode=5", "-o", dst_file, f))
        self._parallel("Making m4a files...", commands, self._m4a_dir)
        for m4a in self._m4a_filenames:
            number = os.path.basename(m4a).split("__")[0]
            song = mutagen.mp4.MP4(m4a)
            track = self._info.get_track(number)
            song.delete()
            song.update(
                {
                    "\xa9ART": self._info.artist,
                    "aART": self._info.artist,
                    "soar": self._info.artist_sort_name,
                    "soaa": self._info.artist_sort_name,
                    "\xa9alb": self._info.album,
                    "\xa9day": str(self._info.year),
                    "\xa9gen": self._info.genre,
                    "\xa9nam": track["title"],
                    "trkn": ((int(track["number"]), len(self._info.tracks)),),
                    "\xa9cmt": self._info.get_comment_string(),
                }
            )
            if self._info.front_cover:
                cover = mutagen.mp4.MP4Cover(self._info.front_cover)
                song["covr"] = [cover]
            song.save()

    def _make_mp3(self):
        commands = []
        for f in self._wav_filenames:
            dst_file = os.path.join(self._mp3_dir, os.path.basename(f).replace(".wav", ".mp3"))
            commands.append(("lame", "--silent", "-h", "-b", "192", f, dst_file))
        self._parallel("Making mp3 files...", commands, self._mp3_dir)
        mutagen.easyid3.EasyID3.RegisterTextKey("comment", "COMM")
        mutagen.easyid3.EasyID3.RegisterTextKey("artistsort", "TSOP")
        mutagen.easyid3.EasyID3.RegisterTextKey("albumartistsort", "TSO2")
        for mp3 in self._mp3_filenames:
            number = os.path.basename(mp3).split("__")[0]
            song = mutagen.mp3.EasyMP3(mp3)
            track = self._info.get_track(number)
            song.delete()
            song.update(
                {
                    "artist": self._info.artist,
                    "albumartist": self._info.artist,
                    "artistsort": self._info.artist_sort_name,
                    "albumartistsort": self._info.artist_sort_name,
                    "album": self._info.album,
                    "date": str(self._info.year),
                    "genre": self._info.genre,
                    "title": track["title"],
                    "tracknumber": f"{track['number']}/{len(self._info.tracks)}",
                    "comment": self._info.get_comment_string(),
                }
            )
            song.save(mp3, v1=2)
            song = mutagen.id3.ID3(mp3)
            song["APIC"] = mutagen.id3.APIC(
                encoding=3,
                mime="image/jpeg",
                type=3,
                desc="front cover",
                data=self._info.front_cover,
            )
            song.save()

    def _make_wav(self):
        commands = [
            ("flac", "--silent", "--decode", f"--output-prefix={self._wav_dir}/", f)
            for f in self._args.files
        ]
        self._parallel("Making wav files...", commands, self._wav_dir)

    def _move_files(self):
        artist_dir = text.get_filename(self._info.artist)
        album_dir = text.get_filename(f"{self._info.year}__{self._info.album}")
        flac_dir = f"library/flac/{artist_dir}/{album_dir}"
        m4a_dir = f"library/m4a/{artist_dir}/{album_dir}"
        mp3_dir = f"library/mp3/{artist_dir}/{album_dir}"
        for d in (flac_dir, m4a_dir, mp3_dir):
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d)
        [os.rename(f, f"{flac_dir}/{os.path.basename(f)}") for f in self._flac_filenames]
        [os.rename(f, f"{m4a_dir}/{os.path.basename(f)}") for f in self._m4a_filenames]
        [os.rename(f, f"{mp3_dir}/{os.path.basename(f)}") for f in self._mp3_filenames]

    def _normalize(self):
        command = ["wavegain", "--album", "--apply"]
        command.extend(glob.glob(self._wav_dir))
        subprocess.run(command)

    @staticmethod
    def _parallel(message, commands, touch=None):
        touch = touch or []
        with Dots(message) as d:
            for p in [subprocess.Popen(c) for c in commands]:
                d.dot()
                p.wait()
        for fn in sorted(glob.glob(os.path.join(touch, "*"))):
            subprocess.run(("touch", fn))

    def _rename_wav(self):
        number = 0
        for filename in self._wav_filenames:
            number += 1
            path, base = os.path.split(filename)
            track = self._info.get_track(str(number).zfill(2))
            new_name = os.path.join(path, f"{track['filename']}.wav")
            if new_name != filename:
                print(f"{os.path.basename(filename)} --> {os.path.basename(new_name)}")
                os.rename(filename, new_name)
