"""

Useful stuff: https://help.mp3tag.de/main_tags.html
"""

import glob
import os
import pprint
import shutil
import subprocess
import sys
import time

import mutagen
import mutagen.easyid3
import mutagen.flac
import mutagen.id3
import mutagen.mp3
import mutagen.mp4

from audiolibrarian import text
from audiolibrarian.discogs import DiscogsInfo
from audiolibrarian.musicbrains import MusicBrainsInfo
from audiolibrarian.output import Dots

TXXX = mutagen.id3.TXXX
UFID = mutagen.id3.UFID


class AudioLibrarian:
    def __init__(self, args):
        self._args = args
        self._source = self._args.source
        self._work_dir = "workdir"
        self._flac_dir = os.path.join(self._work_dir, "flac")
        self._m4a_dir = os.path.join(self._work_dir, "m4a")
        self._mp3_dir = os.path.join(self._work_dir, "mp3")
        self._wav_dir = os.path.join(self._work_dir, "wav")
        self._lock_file = "workdir.lock"
        d = self._args.disc
        self._disc_number, self._disc_count = d.split("/") if d else ("1", "1")

        # if we're given a directory, grab all the flac files therein
        if (
            self._source == "files"
            and len(self._args.filenames) == 1
            and os.path.isdir(self._args.filenames[0])
        ):
            self._args.filenames = sorted(
                glob.glob(os.path.join(self._args.filenames[0], "*.flac"))
            )

        artist, album = self._get_artist_album()
        pprint.pp([os.path.basename(f) for f in self._args.filenames])
        if args.db == "discogs":
            self._info = DiscogsInfo(artist, album, self._disc_number, args.verbose)
        else:
            self._info = MusicBrainsInfo(artist, album, self._disc_number, args.verbose)
        pprint.pp(self._info)
        if len(self._args.filenames) != len(self._info.tracks):
            print("\n*** Track count does not match file count ***\n")
        if input("Confirm [Y,n]: ").lower() == "n":
            return

        self._acquire_lock()
        try:
            self._make_clean_workdirs()
            self._make_wav()
            self._rename_wav()
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
        for filename in self._args.filenames:
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
        for d in self._flac_dir, self._m4a_dir, self._mp3_dir, self._wav_dir:
            os.makedirs(d)

    def _make_flac(self):
        commands = [
            ("flac", "--silent", f"--output-prefix={self._flac_dir}/", f)
            for f in self._wav_filenames
        ]
        self._parallel("Making flac files...", commands, self._flac_dir)
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
        for flac in self._flac_filenames:
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
        self._parallel("Making m4a files...", commands, self._m4a_dir)
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
        self._parallel("Making mp3 files...", commands, self._mp3_dir)
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

    def _make_wav(self):
        tmp_dir = os.path.join(self._wav_dir, "tmp")
        os.makedirs(tmp_dir)
        commands = [
            ("flac", "--silent", "--decode", f"--output-prefix={self._wav_dir}/tmp/", f)
            for f in self._args.filenames
        ]
        self._parallel("Making wav files...", commands, self._wav_dir)
        for f in glob.glob(os.path.join(tmp_dir, "*.wav")):
            r = subprocess.run(("sndfile-convert", "-pcm16", f, f.replace("/tmp/", "/")))
            r.check_returncode()
        shutil.rmtree(tmp_dir)

    def _move_files(self):
        artist_dir = text.get_filename(self._info.artist)
        album_dir = text.get_filename(f"{self._info.original_year}__{self._info.album}")
        flac_dir = f"library/flac/{artist_dir}/{album_dir}"
        m4a_dir = f"library/m4a/{artist_dir}/{album_dir}"
        mp3_dir = f"library/mp3/{artist_dir}/{album_dir}"
        if self._args.disc:
            flac_dir += f"/disc{self._disc_number}"
            m4a_dir += f"/disc{self._disc_number}"
            mp3_dir += f"/disc{self._disc_number}"
        for d in (flac_dir, m4a_dir, mp3_dir):
            if os.path.isdir(d):
                shutil.rmtree(d)
            os.makedirs(d)
        [os.rename(f, f"{flac_dir}/{os.path.basename(f)}") for f in self._flac_filenames]
        [os.rename(f, f"{m4a_dir}/{os.path.basename(f)}") for f in self._m4a_filenames]
        [os.rename(f, f"{mp3_dir}/{os.path.basename(f)}") for f in self._mp3_filenames]

    def _normalize(self):
        print("Normalizing wav files...")
        command = ["wavegain", "--album", "--apply"]
        command.extend(glob.glob(self._wav_dir))
        r = subprocess.run(command, stdout=subprocess.DEVNULL)
        r.check_returncode()

    @staticmethod
    def _parallel(message, commands, touch=None):
        touch = touch or []
        with Dots(message) as d:
            for p in [subprocess.Popen(c) for c in commands]:
                d.dot()
                p.wait()
        for fn in sorted(glob.glob(os.path.join(touch, "*"))):
            subprocess.run(("touch", fn))

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
