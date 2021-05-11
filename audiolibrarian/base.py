"""AudioLibrarian base class.

Useful stuff: https://help.mp3tag.de/main_tags.html
"""
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

import argparse
import logging
import pathlib
import shutil
import subprocess
import sys
import warnings
from collections.abc import Iterable
from typing import Union

import filelock
import pyaml
import yaml

# noinspection PyPackageRequirements
from colors import color

from audiolibrarian import audiofile, cmd, musicbrainz, records, text

log = logging.getLogger(__name__)


class Base:  # pylint: disable=too-many-instance-attributes,too-few-public-methods
    """AudioLibrarian base class.

    This class should be sub-classed for various sub_commands.
    """

    command = None

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize the base."""
        # Pull in stuff from args
        search_keys = ("album", "artist", "mb_artist_id", "mb_release_id")
        self._provided_search_data = {k: v for k, v in vars(args).items() if k in search_keys}
        if vars(args).get("disc"):
            self._disc_number, self._disc_count = [int(x) for x in args.disc.split("/")]
        else:
            self._disc_number, self._disc_count = 1, 1

        # directories
        self._library_dir = pathlib.Path("library").resolve()
        self._work_dir = pathlib.Path("/var/tmp/audiolibrarian")
        self._flac_dir = self._work_dir / "flac"
        self._m4a_dir = self._work_dir / "m4a"
        self._mp3_dir = self._work_dir / "mp3"
        self._source_dir = self._work_dir / "source"
        self._wav_dir = self._work_dir / "wav"
        self._manifest_file = "Manifest.yaml"
        self._lock = filelock.FileLock(str(self._work_dir) + ".lock")

        # initialize stuff that will be defined later
        self._audio_source = None
        self._release = None
        self._medium = None
        self._source_is_cd = None
        self._source_example = None

    @property
    def _flac_filenames(self) -> list[pathlib.Path]:
        # Return the current list of flac files in the work directory.
        return sorted(self._flac_dir.glob("*.flac"), key=text.alpha_numeric_key)

    @property
    def _m4a_filenames(self) -> list[pathlib.Path]:
        # Return the current list of m4a files in the work directory.
        return sorted(self._m4a_dir.glob("*.m4a"), key=text.alpha_numeric_key)

    @property
    def _mp3_filenames(self) -> list[pathlib.Path]:
        # Return the current list of mp3 files in the work directory.
        return sorted(self._mp3_dir.glob("*.mp3"), key=text.alpha_numeric_key)

    @property
    def _multi_disc(self) -> bool:
        # Return True if this is part of a multi-disc set.
        return (self._disc_number, self._disc_count) != (1, 1)

    @property
    def _source_filenames(self) -> list[pathlib.Path]:
        # Return the current list of source files in the work directory.
        return sorted(self._source_dir.glob("*.flac"), key=text.alpha_numeric_key)

    @property
    def _wav_filenames(self) -> list[pathlib.Path]:
        # Return the current list of wav files in the work directory.
        return sorted(self._wav_dir.glob("*.wav"), key=text.alpha_numeric_key)

    def _convert(self, make_source: bool = True) -> None:
        # Performs all of the steps of ripping, normalizing, converting and moving the files.
        if self._audio_source is None:
            warnings.warn("Cannot convert; no audio_source is defined.", RuntimeWarning)
            return
        self._audio_source.prepare_source()
        with self._lock:
            self._make_clean_workdirs()
            self._audio_source.copy_wavs(self._wav_dir)
            self._rename_wav()
            if make_source:
                self._make_source()
            self._normalize()
            self._make_flac()
            self._make_m4a()
            self._make_mp3()
            self._move_files(move_source=make_source)

    @staticmethod
    def _find_audio_files(
        directories: list[Union[str, pathlib.Path]]
    ) -> Iterable[audiofile.AudioFile]:
        # Yields audiofile objects found in the given directories.
        paths = []
        # grab all of the paths first because thing may change as files are renamed
        for directory in directories:
            path = pathlib.Path(directory)
            for ext in audiofile.extensions:
                paths.extend(path.rglob(f"*{ext}"))
        paths = sorted(list(set(paths)))
        # using yield rather than returning a list saves us from simultaneously storing
        # potentially thousands of AudioFile objects in memory at the same time
        for path in paths:
            try:
                yield audiofile.open_(path)
            except FileNotFoundError:
                continue

    def _find_manifests(self, directories: list[Union[str, pathlib.Path]]) -> list[pathlib.Path]:
        # Return a sorted, unique list of manifest files anywhere in the given directories.
        manifests = set()
        for directory in directories:
            path = pathlib.Path(directory)
            for manifest in path.rglob(self._manifest_file):
                manifests.add(manifest)
        return sorted(list(manifests))

    def _get_searcher(self) -> musicbrainz.Searcher:
        # Return a Searcher object populated with data from the audio source and cli args.
        search_data = self._audio_source.get_search_data() if self._audio_source else {}
        searcher = musicbrainz.Searcher(**search_data)
        searcher.disc_number = self._disc_number
        # override with user-provided info
        if value := self._provided_search_data.get("artist"):
            searcher.artist = value
        if value := self._provided_search_data.get("album"):
            searcher.album = value
        if value := self._provided_search_data.get("mb_artist_id"):
            searcher.mb_artist_id = value
        if value := self._provided_search_data.get("mb_release_id"):
            searcher.mb_release_id = value
        log.info(f"SEARCHER: {searcher}")
        return searcher

    def _get_tag_info(self) -> None:
        print("Gathering search information...")
        searcher = self._get_searcher()
        skip_confirm = bool(searcher.mb_artist_id and searcher.mb_release_id)
        print("Finding MusicBrainz release information...")
        self._release = searcher.find_music_brains_release()
        self._medium = self._release.media[int(self._disc_number)]
        if cover := not self._release.front_cover and self._audio_source.get_front_cover():
            log.info("Using front-cover image from source file")
            self._release.front_cover = cover
        summary, okay = self._summary()
        print(summary)
        if not okay:
            print(color("\n*** Track count does not match file count ***\n", fg="red"))
            skip_confirm = False
        if not skip_confirm and text.input_("Confirm [N,y]: ").lower() != "y":  # pragma: no cover
            sys.exit(1)

    def _make_clean_workdirs(self) -> None:
        # Erases everything from the workdir and creates the empty directory structure.
        if self._work_dir.is_dir():
            shutil.rmtree(self._work_dir)
        for path in self._flac_dir, self._m4a_dir, self._mp3_dir, self._source_dir, self._wav_dir:
            path.mkdir(parents=True)

    def _make_flac(self, source: bool = False) -> None:
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

    def _make_m4a(self) -> None:
        # Converts the wav files into m4a files; tags them.
        commands = []
        for filename in self._wav_filenames:
            dst_file = self._m4a_dir / filename.name.replace(".wav", ".m4a")
            commands.append(("fdkaac", "--silent", "--bitrate-mode=5", "-o", dst_file, filename))
        cmd.parallel(f"Making {len(commands)} m4a files...", commands)
        cmd.touch(self._m4a_filenames)
        self._tag_files(self._m4a_filenames)

    def _make_mp3(self) -> None:
        # Converts the wav files into mp3 files; tags them.
        commands = []
        for filename in self._wav_filenames:
            dst_file = self._mp3_dir / filename.name.replace(".wav", ".mp3")
            commands.append(("lame", "--silent", "-h", "-b", "192", filename, dst_file))
        cmd.parallel(f"Making {len(commands)} mp3 files...", commands)
        cmd.touch(self._mp3_filenames)
        self._tag_files(self._mp3_filenames)

    def _make_source(self) -> None:
        # Converts the files into flac files; stores them in the source dir; reads their tags.
        #
        # The files are defined by the audio source; they could be wav files from a CD
        # or another type of audio file.
        self._make_flac(source=True)
        self._source_example = audiofile.open_(self._source_filenames[0]).read_tags()

    def _move_files(self, move_source: bool = True) -> None:
        # Moves converted/tagged files from the work directory into the library directory.
        artist_album_dir = self._release.get_artist_album_path()
        flac_dir = self._library_dir / "flac" / artist_album_dir
        m4a_dir = self._library_dir / "m4a" / artist_album_dir
        mp3_dir = self._library_dir / "mp3" / artist_album_dir
        source_dir = self._library_dir / "source" / artist_album_dir
        if self._multi_disc:
            flac_dir /= f"disc{self._disc_number}"
            m4a_dir /= f"disc{self._disc_number}"
            mp3_dir /= f"disc{self._disc_number}"
            source_dir /= f"disc{self._disc_number}"
        for path in [flac_dir, m4a_dir, mp3_dir] + ([source_dir] if move_source else []):
            if path.is_dir():
                shutil.rmtree(path)
            path.mkdir(parents=True)
        for path in self._flac_filenames:
            path.rename(flac_dir / path.name)
        for path in self._m4a_filenames:
            path.rename(m4a_dir / path.name)
        for path in self._mp3_filenames:
            path.rename(mp3_dir / path.name)
        if move_source:
            for path in self._source_filenames:
                path.rename(source_dir / path.name)

    def _normalize(self) -> None:
        # Normalizes the wav files using wavegain.
        print("Normalizing wav files...")
        # sub_command = ["wavegain", "--album", "--apply"]
        command = ["wavegain", "--radio", "--gain=5", "--apply"]
        command.extend(self._wav_filenames)
        result = subprocess.run(command, capture_output=True, check=False)
        for line in str(result.stderr).split(r"\n"):
            line_trunc = line[:137] + "..." if len(line) > 140 else line
            log.info(f"WAVEGAIN: {line_trunc}")
        result.check_returncode()

    @staticmethod
    def _read_manifest(manifest_path: pathlib.Path) -> dict:
        with open(manifest_path, "r") as manifest_file:
            return yaml.safe_load(manifest_file)

    def _rename_wav(self) -> None:
        # Renames the wav files to a filename-sane representation of the track title.
        for old_path in self._wav_filenames:
            track_number = text.get_track_number(str(old_path.name))
            title_filename = self._medium.tracks[track_number].get_filename(".wav")
            new_path = old_path.parent / title_filename
            if new_path.resolve() != old_path.resolve():
                log.info(f"RENAMING: {old_path.name} --> {new_path.name}")
                old_path.rename(new_path)

    def _summary(self) -> tuple[str, bool]:  # pylint: disable=too-many-locals
        # Return a summary of the conversion/tagging process and an "ok" flag indicating issues.
        #
        # The summary is a nicely formatted table showing the album, artist and track info.
        # The "ok" flag indicating issues will be true if:
        #   - the file count does not match the song count from the MusicBrainz database
        # (https://jrgraphix.net/r/Unicode/2500-257F)
        if self._audio_source is None or self._release is None:
            warnings.warn(
                "Cannot provide summary; missing audio_source and/or release.", RuntimeWarning
            )
            return "", False
        lines = []
        okay = True
        no_match = "(no match)"
        col1 = [f.stem if f else no_match for f in self._audio_source.source_list]
        col2 = [t.get_filename() for _, t in sorted(self._medium.tracks.items())]
        col3 = [f"{str(n).zfill(2)}: {t.title}" for n, t in sorted(self._medium.tracks.items())]
        min_total_w = 74  # make sure we've got enough width for MB Release URL
        width = 40
        col1_w = min(width, max([len(x) for x in col1] + [len(no_match)]))
        col2_w = min(width, max([len(x) for x in col2] + [len(no_match)]))
        col3_w = min(width, max([len(x) for x in col3] + [len(no_match)]))
        if col1_w + col2_w + col3_w < min_total_w:
            col3_w = min_total_w - (col1_w + col2_w)
        tab_w = col1_w + col2_w + col3_w + 6
        c1_line = (col1_w + 2) * "\u2550"
        c2_line = (col2_w + 2) * "\u2550"
        c3_line = (col3_w + 2) * "\u2550"
        alb = f"Album:      {self._release.album}"
        art = f"Artist(s):  {', '.join(self._release.album_artists_sort)}"
        med = f"Disc:       {self._disc_number} of {self._disc_count}"
        mbr = f"MB Release: https://musicbrainz.org/release/{self._release.musicbrainz_album_id}"
        lines.append(f"\u2554{c1_line}\u2550{c2_line}\u2550{c3_line}\u2557")
        for line in (alb, art, mbr, med):
            lines.append(f"\u2551 {line} {' ' * (tab_w - len(line))}\u2551")
        fmt = f"\u2551 {{c1: <{col1_w}}} \u2502 {{c2: <{col2_w}}} \u2502 {{c3: <{col3_w}}} \u2551"
        lines.append(f"\u2560{c1_line}\u2564{c2_line}\u2564{c3_line}\u2563")
        lines.append(fmt.format(c1="Source", c2="Destination", c3="Title"))
        lines.append(f"\u2560{c1_line}\u256A{c2_line}\u256A{c3_line}\u2563")
        rows = max(len(col1), len(col2), len(col3))
        for i in range(rows):
            col1_ = (
                ((col1[i][: width - 3] + "...") if len(col1[i]) > width else col1[i])
                if len(col1) > i
                else no_match
            )
            col2_ = (
                ((col2[i][: width - 3] + "...") if len(col2[i]) > width else col2[i])
                if len(col2) > i
                else no_match
            )
            col3_ = (
                ((col3[i][: width - 3] + "...") if len(col3[i]) > width else col3[i])
                if len(col3) > i
                else no_match
            )
            lines.append(fmt.format(c1=col1_, c2=col2_, c3=col3_))
            if no_match in (col1_, col2_, col3_):
                okay = False
        lines.append(f"\u255A{c1_line}\u2567{c2_line}\u2567{c3_line}\u255D")
        return "\n".join(lines), okay

    def _tag_files(self, filenames: list[pathlib.Path]) -> None:
        # Tags the given list of files.
        for filename in filenames:
            song = audiofile.open_(filename)
            song.one_track = records.OneTrack(
                release=self._release,
                medium_number=self._disc_number,
                track_number=int(filename.name.split("__")[0]),
            )
            song.write_tags()

    def _write_manifest(self) -> None:
        # Writes out a manifest file with release information.
        release = self._release  # we use this a lot below
        file_info = self._source_example.track.file_info
        manifest = {
            "album": release.album,
            "artist": release.album_artists.first,
            "artist_sort_name": release.album_artists_sort.first,
            "media": release.media[self._disc_number].formats.first,
            "genre": release.genres.first,
            "disc_number": self._disc_number,
            "disc_total": self._disc_count,
            "original_year": release.original_year,
            "date": release.date,
            "musicbrainz_info": {
                "albumid": release.musicbrainz_album_id,
                "albumartistid": release.musicbrainz_album_artist_ids.first,
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
            artist_album_dir = self._release.get_artist_album_path()
            manifest_filename = source_dir / artist_album_dir / self._manifest_file
        with open(manifest_filename, "w") as manifest_file:
            pyaml.dump(manifest, manifest_file)
        print(f"Wrote {manifest_filename}")
