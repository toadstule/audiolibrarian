"""

Useful stuff: https://help.mp3tag.de/main_tags.html
"""
import shutil
import subprocess
import sys
from logging import getLogger
from pathlib import Path
from typing import List, Tuple

import pyaml

# noinspection PyPackageRequirements
from colors import color
from filelock import FileLock

from audiolibrarian import cmd, text
from audiolibrarian.audiofile import open_
from audiolibrarian.musicbrainz import Searcher
from audiolibrarian.records import OneTrack

log = getLogger(__name__)


class Base:
    """AudioLibrarian base class.

    This class should be sub-classed for various sub_commands.
    """

    command = None

    def __init__(self, args):
        # Pull in stuff from args
        self._provided_search_data = {
            "album": args.album,
            "artist": args.artist,
            "mb_artist_id": args.mb_artist_id,
            "mb_release_id": args.mb_release_id,
        }
        if args.disc:
            self._disc_number, self._disc_count = map(int, args.disc.split("/"))
            self._multi_disc = True
        else:
            self._disc_number, self._disc_count = 1, 1
            self._multi_disc = False

        # directories
        self._library_dir = Path("library").resolve()
        self._work_dir = Path("/var/tmp/audiolibrarian")
        self._flac_dir = self._work_dir / "flac"
        self._m4a_dir = self._work_dir / "m4a"
        self._mp3_dir = self._work_dir / "mp3"
        self._source_dir = self._work_dir / "source"
        self._wav_dir = self._work_dir / "wav"
        self._manifest_file = "Manifest.yaml"
        self._lock = FileLock(str(self._work_dir) + ".lock")

        # initialize stuff that will be defined later
        self._audio_source = None
        self._release = None
        self._medium = None
        self._source_is_cd = None
        self._source_example = None

    @property
    def _flac_filenames(self):
        # Returns the current list of flac files in the work directory.
        return sorted(self._flac_dir.glob("*.flac"), key=text.alpha_numeric_key)

    @property
    def _m4a_filenames(self):
        # Returns the current list of m4a files in the work directory.
        return sorted(self._m4a_dir.glob("*.m4a"), key=text.alpha_numeric_key)

    @property
    def _mp3_filenames(self):
        # Returns the current list of mp3 files in the work directory.
        return sorted(self._mp3_dir.glob("*.mp3"), key=text.alpha_numeric_key)

    @property
    def _source_filenames(self):
        # Returns the current list of source files in the work directory.
        return sorted(self._source_dir.glob("*.flac"), key=text.alpha_numeric_key)

    @property
    def _wav_filenames(self):
        # Returns the current list of wav files in the work directory.
        return sorted(self._wav_dir.glob("*.wav"), key=text.alpha_numeric_key)

    def _convert(self):
        # Performs all of the steps of ripping, normalizing, converting and moving the files.
        self._audio_source.prepare_source()
        with self._lock:
            self._make_clean_workdirs()
            self._audio_source.copy_wavs(self._wav_dir)
            self._rename_wav()
            self._make_source()
            self._normalize()
            self._make_flac()
            self._make_m4a()
            self._make_mp3()
            self._move_files()

    def _get_searcher(self) -> Searcher:
        # Returns a Searcher object populated with data from the audio source and cli args.
        search_data = self._audio_source.get_search_data()
        searcher = Searcher(**search_data)
        searcher.disc_number = self._disc_number
        # override with user-provided info
        if value := self._provided_search_data["artist"]:
            searcher.artist = value
        if value := self._provided_search_data["album"]:
            searcher.album = value
        if value := self._provided_search_data["mb_artist_id"]:
            searcher.mb_artist_id = value
        if value := self._provided_search_data["mb_release_id"]:
            searcher.mb_release_id = value
        log.info(f"SEARCHER: {searcher}")
        return searcher

    def _get_tag_info(self):
        print("Gathering search information...")
        searcher = self._get_searcher()
        skip_confirm = bool(searcher.mb_artist_id and searcher.mb_release_id)
        print("Finding MusicBrainz release information...")
        self._release = searcher.find_music_brains_release()
        self._medium = self._release.media[int(self._disc_number)]
        summary, ok = self._summary()
        print(summary)
        if not ok:
            print(color("\n*** Track count does not match file count ***\n", fg="red"))
            skip_confirm = False
        if not skip_confirm and input("Confirm [N,y]: ").lower() != "y":
            sys.exit(1)

    def _make_clean_workdirs(self):
        # Erases everything from the workdir and creates the empty directory structure.
        if self._work_dir.is_dir():
            shutil.rmtree(self._work_dir)
        for d in self._flac_dir, self._m4a_dir, self._mp3_dir, self._source_dir, self._wav_dir:
            d.mkdir(parents=True)

    def _make_flac(self, source=False):
        # Converts the wav files into flac files; tags them.
        #
        # If source is True, it stores the flac files in the source directory,
        # otherwise it stores them in the flac directory.
        out_dir = self._source_dir if source else self._flac_dir
        commands = [
            ("flac", "--silent", f"--output-prefix={out_dir}/", f) for f in self._wav_filenames
        ]
        cmd.parallel(f"Making {len(self._wav_filenames)} flac files...", commands)
        filenames = self._source_filenames if source else self._flac_filenames
        cmd.touch(filenames)
        self._tag_files(filenames)

    def _make_m4a(self):
        # Converts the wav files into m4a files; tags them.
        commands = []
        for f in self._wav_filenames:
            dst_file = self._m4a_dir / f.name.replace(".wav", ".m4a")
            commands.append(("fdkaac", "--silent", "--bitrate-mode=5", "-o", dst_file, f))
        cmd.parallel(f"Making {len(commands)} m4a files...", commands)
        cmd.touch(self._m4a_filenames)
        self._tag_files(self._m4a_filenames)

    def _make_mp3(self):
        # Converts the wav files into mp3 files; tags them.
        commands = []
        for f in self._wav_filenames:
            dst_file = self._mp3_dir / f.name.replace(".wav", ".mp3")
            commands.append(("lame", "--silent", "-h", "-b", "192", f, dst_file))
        cmd.parallel(f"Making {len(commands)} mp3 files...", commands)
        cmd.touch(self._mp3_filenames)
        self._tag_files(self._mp3_filenames)

    def _make_source(self):
        # Converts the files into flac files; stores them in the source dir; reads their tags.
        #
        # The files are defined by the audio source; they could be wav files from a CD
        # or another type of audio file.
        self._make_flac(source=True)
        self._source_example = open_(self._source_filenames[0]).read_tags()

    def _move_files(self):
        # Moves converted/tagged files from the work directory into the library directory.
        artist_dir = text.get_filename(self._release.first("album_artists"))
        album_dir = text.get_filename(f"{self._release.original_year}__{self._release.album}")
        flac_dir = self._library_dir / "flac" / artist_dir / album_dir
        m4a_dir = self._library_dir / "m4a" / artist_dir / album_dir
        mp3_dir = self._library_dir / "mp3" / artist_dir / album_dir
        source_dir = self._library_dir / "source" / artist_dir / album_dir
        if self._multi_disc:
            flac_dir /= f"disc{self._disc_number}"
            m4a_dir /= f"disc{self._disc_number}"
            mp3_dir /= f"disc{self._disc_number}"
            source_dir /= f"disc{self._disc_number}"
        for d in (flac_dir, m4a_dir, mp3_dir, source_dir):
            if d.is_dir():
                shutil.rmtree(d)
            d.mkdir(parents=True)
        [f.rename(flac_dir / f.name) for f in self._flac_filenames]
        [f.rename(m4a_dir / f.name) for f in self._m4a_filenames]
        [f.rename(mp3_dir / f.name) for f in self._mp3_filenames]
        [f.rename(source_dir / f.name) for f in self._source_filenames]

    def _normalize(self):
        # Normalizes the wav files using wavegain.
        print("Normalizing wav files...")
        # sub_command = ["wavegain", "--album", "--apply"]
        command = ["wavegain", "--radio", "--gain=5", "--apply"]
        command.extend(self._wav_filenames)
        r = subprocess.run(command, capture_output=True)
        for line in str(r.stderr).split(r"\n"):
            line_trunc = line[:137] + "..." if len(line) > 140 else line
            log.info(f"WAVEGAIN: {line_trunc}")
        r.check_returncode()

    def _rename_wav(self):
        # Renames the wav files to a filename-sane representation of the track title.
        for track_number, old_path in enumerate(self._wav_filenames, 1):
            title_filename = self._medium.tracks[track_number].get_filename() + ".wav"
            new_path = old_path.parent / title_filename
            if new_path.resolve() != old_path.resolve():
                log.info(f"RENAMING: {old_path.name} --> {new_path.name}")
                old_path.rename(new_path)

    def _summary(self) -> Tuple[str, bool]:
        # Returns a summary of the conversion/tagging process and an "ok" flag indicating issues.
        #
        # The summary is a nicely formatted table showing the album, artist and track info.
        # The "ok" flag indicating issues will be true if:
        #   - the file count does not match the song count from the MusicBrainz database
        lines = []
        ok = True
        source_filenames = self._audio_source.get_source_filenames()
        col1 = [f.stem for f in source_filenames]
        col2 = [t.get_filename() for _, t in sorted(self._medium.tracks.items())]
        col3 = [f"{str(n).zfill(2)}: {t.title}" for n, t in sorted(self._medium.tracks.items())]
        min_total_w = 74  # make sure we've got enough width for MB Release URL
        w = 40
        no_match = "(no match)"
        col1_w = min(w, max([len(x) for x in col1] + [len(no_match)]))
        col2_w = min(w, max([len(x) for x in col2] + [len(no_match)]))
        col3_w = min(w, max([len(x) for x in col3] + [len(no_match)]))
        if col1_w + col2_w + col3_w < min_total_w:
            col3_w = min_total_w - (col1_w + col2_w)
        tab_w = col1_w + col2_w + col3_w + 6
        c1_line = (col1_w + 2) * "\u2550"
        c2_line = (col2_w + 2) * "\u2550"
        c3_line = (col3_w + 2) * "\u2550"
        alb = f"Album:      {self._release.album}"
        art = f"Artist(s):  {', '.join(self._release.album_artists)}"
        med = f"Disc:       {self._disc_number} of {self._disc_count}"
        mbr = f"MB Release: https://musicbrainz.org/release/{self._release.musicbrainz_album_id}"
        lines.append(f"\u2554{c1_line}\u2550{c2_line}\u2550{c3_line}\u2557")
        for x in (alb, art, mbr, med):
            lines.append(f"\u2551 {x} {' ' * (tab_w - len(x))}\u2551")
        lines.append(f"\u2560{c1_line}\u2564{c2_line}\u2564{c3_line}\u2563")
        fmt = f"\u2551 {{c1: <{col1_w}}} \u2502 {{c2: <{col2_w}}} \u2502 {{c3: <{col3_w}}} \u2551"
        rows = max(len(col1), len(col2), len(col3))
        for i in range(rows):
            c1 = (
                ((col1[i][: w - 3] + "...") if len(col1[i]) > w else col1[i])
                if len(col1) > i
                else no_match
            )
            c2 = (
                ((col2[i][: w - 3] + "...") if len(col2[i]) > w else col2[i])
                if len(col2) > i
                else no_match
            )
            c3 = (
                ((col3[i][: w - 3] + "...") if len(col3[i]) > w else col3[i])
                if len(col3) > i
                else no_match
            )
            lines.append(fmt.format(c1=c1, c2=c2, c3=c3))
            if no_match in (c1, c2, c3):
                ok = False
        lines.append(f"\u255A{c1_line}\u2567{c2_line}\u2567{c3_line}\u255D")
        return "\n".join(lines), ok

    def _tag_files(self, filenames: List[Path]) -> None:
        # Tags the given list of files.
        for f in filenames:
            song = open_(f)
            song.one_track = OneTrack(
                release=self._release,
                medium_number=self._disc_number,
                track_number=int(f.name.split("__")[0]),
            )
            song.write_tags()

    def _write_manifest(self):
        # Writes out a manifest file with release information.
        release = self._release  # we use this a lot below
        file_info = self._source_example.track.file_info
        manifest = {
            "album": release.album,
            "artist": release.first("album_artists"),
            "artist_sort_name": release.first("album_artists_sort"),
            "media": release.media[self._disc_number].first("formats"),
            "genre": release.first("genres"),
            "disc_number": self._disc_number,
            "disc_total": self._disc_count,
            "original_year": release.original_year,
            "date": release.date,
            "musicbrainz_info": {
                "albumid": release.musicbrainz_album_id,
                "albumartistid": release.first("musicbrainz_album_artist_ids"),
                "releasegroupid": release.musicbrainz_release_group_id,
            },
            "source_info": {
                "type": file_info.type.name,
                "bitrate": file_info.bitrate,
                "bitrate_mode": file_info.bitrate_mode.name,
            },
        }
        if self.command == "manifest":
            manifest_filename = self._manifest_file  # write to current directory
            if self._source_is_cd:
                manifest["source_info"] = {
                    "type": "CD",
                    "bitrate": 1411,
                    "bitrate_mode": "CBR",
                }
        else:
            source_dir = self._library_dir / "source"
            artist_dir = text.get_filename(self._release.first("album_artists"))
            album_dir = text.get_filename(f"{self._release.original_year}__{self._release.album}")
            manifest_filename = source_dir / artist_dir / album_dir / self._manifest_file
        with open(manifest_filename, "w") as manifest_file:
            pyaml.dump(manifest, manifest_file)
        print(f"Wrote {manifest_filename}")
