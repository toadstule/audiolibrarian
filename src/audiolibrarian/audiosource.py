"""AudioSource."""

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
import abc
import logging
import os
import pathlib
import shutil
import subprocess
import tempfile
from collections.abc import Callable  # noqa: TC003

import discid

from audiolibrarian import audiofile, records, sh, text
from audiolibrarian.settings import SETTINGS

log = logging.getLogger(__name__)


class AudioSource(abc.ABC):
    """An abstract base class for AudioSource classes."""

    def __init__(self) -> None:
        """Initialize an AudioSource."""
        self._temp_dir: pathlib.Path = pathlib.Path(tempfile.mkdtemp())
        self._source_list: list[pathlib.Path | None] | None = None

    def __del__(self) -> None:
        """Remove any temp files."""
        if self._temp_dir.is_dir():
            shutil.rmtree(self._temp_dir)

    @property
    def source_list(self) -> list[pathlib.Path | None]:
        """Return a list with source file paths and blanks.

        The list will be ordered by track number, with None in spaces where no
        filename is present for that track number.
        """
        if not self._source_list:
            source_filenames = self.get_source_filenames()
            length = max(text.get_track_number(str(f.name)) for f in source_filenames)
            result: list[pathlib.Path | None] = [None] * length
            if length:
                for filename in source_filenames:
                    idx = text.get_track_number(str(filename.name)) - 1
                    result[idx] = filename
            self._source_list = result
        return self._source_list

    def copy_wavs(self, dest_dir: pathlib.Path) -> None:
        """Copy wav files to the given destination directory."""
        for filename in self.get_wav_filenames():
            shutil.copy2(filename, dest_dir / filename.name)

    def get_front_cover(self) -> records.FrontCover | None:
        """Return a FrontCover record or None."""
        return None

    @abc.abstractmethod
    def get_search_data(self) -> dict[str, str]:
        """Return a dictionary of search data useful for doing a MusicBrainz search."""

    @abc.abstractmethod
    def get_source_filenames(self) -> list[pathlib.Path]:
        """Return a list of the original source file paths."""

    def get_wav_filenames(self) -> list[pathlib.Path]:
        """Return a list of the prepared wav file paths."""
        return sorted(self._temp_dir.glob("*.wav"), key=text.alpha_numeric_key)

    @abc.abstractmethod
    def prepare_source(self) -> None:
        """Convert the source to wav files."""


class CDAudioSource(AudioSource):
    """AudioSource from a compact disc."""

    def __init__(self) -> None:
        """Initialize a CDAudioSource."""
        super().__init__()
        self._cd = discid.read(SETTINGS.discid_device, features=["mcn"])

    def get_search_data(self) -> dict[str, str]:
        """Return a dictionary of search data useful for doing a MusicBrainz search."""
        return {"disc_id": self._cd.id, "disc_mcn": self._cd.mcn}

    def get_source_filenames(self) -> list[pathlib.Path]:
        """Return a list of the original source file paths.

        Since we're working with a CD, these files may not yet exist if they have not been
        read from the disc.
        """
        return [
            self._temp_dir / f"track{str(n + 1).zfill(2)}.cdda.wav"
            for n in range(self._cd.last_track_num)
        ]

    def prepare_source(self) -> None:
        """Pull audio from the CD to wav files."""
        cwd = pathlib.Path.cwd()
        os.chdir(self._temp_dir)
        try:
            subprocess.run(("cd-paranoia", "-B"), check=True)
        finally:
            os.chdir(cwd)
        subprocess.run(("eject",), check=False)


class FilesAudioSource(AudioSource):
    """AudioSource from local files."""

    def __init__(self, filenames: list[pathlib.Path]) -> None:
        """Initialize a FilesAudioSource."""
        super().__init__()
        self._filenames = filenames
        if len(filenames) == 1 and filenames[0].is_dir():
            # If we're given a directory, figure out what's in there.
            for file_type in ("flac", "wav", "m4a", "mp3"):
                if fns := sorted(filenames[0].glob(f"*.{file_type}"), key=text.alpha_numeric_key):
                    self._filenames = list(fns)
                    break
        self._file_type = self._filenames[0].suffix.lstrip(".")

    def get_front_cover(self) -> records.FrontCover | None:
        """Return a FrontCover record or None."""
        for filename in self._filenames:
            one_track = audiofile.AudioFile.open(filename).one_track
            release = one_track.release
            if release.front_cover:
                return release.front_cover
        return None

    def get_search_data(self) -> dict[str, str]:
        """Return a dictionary of search data useful for doing a MusicBrainz search."""
        for filename in self._filenames:
            one_track = audiofile.AudioFile.open(filename).one_track
            release = one_track.release
            track = one_track.track

            artist = track.artist or track.artists.first or "" if track else ""
            album = release.album or "" if release else ""
            mb_artist_id = (
                release.musicbrainz_album_artist_ids.first
                if release and release.musicbrainz_album_artist_ids
                else "" or track.musicbrainz_artist_ids.first
                if track and track.musicbrainz_artist_ids
                else "" or ""
            )
            mb_release_id = release.musicbrainz_album_id or "" if release else ""
            log.info("Artist from tags: %s", artist)
            log.info("Album from tags: %s", album)
            log.info("MB Artist ID from tags: %s", mb_artist_id)
            log.info("MB Release ID from tags: %s", mb_release_id)
            if mb_artist_id and mb_release_id:
                return {"mb_artist_id": mb_artist_id, "mb_release_id": mb_release_id}
            if artist and album:
                return {"artist": artist, "album": album}
        return {}

    def get_source_filenames(self) -> list[pathlib.Path]:
        """Return a list of the original source file paths."""
        return self._filenames

    def prepare_source(self) -> None:
        """Convert the source files to wav files.

        Raises:
             ValueError if the file type is not supported.
        """
        decoders: dict[str, Callable[[str, str], tuple[str, ...]]] = {
            "flac": lambda i, o: ("flac", "--silent", "--decode", f"--output-name={o}", i),
            "m4a": lambda i, o: ("faad", "-q", "-o", o, i),
            "mp3": lambda i, o: ("mpg123", "-q", "-w", o, i),
        }
        try:
            decode = decoders[self._file_type]
        except KeyError as err:
            msg = f"Unsupported source file type: {self._file_type}"
            raise ValueError(msg) from err
        tmp_dir = self._temp_dir / "__tmp__"
        tmp_dir.mkdir(parents=True)
        commands: list[tuple[str, ...]] = []
        for track_number, filepath in enumerate(self.source_list, 1):
            if filepath:
                in_ = str(filepath)
                out_path = tmp_dir / f"{str(track_number).zfill(2)}__.wav"
                out = str(out_path)
                commands.append(decode(in_, out))
                log.info("DECODING: %s -> %s", filepath.name, out_path.name)
        sh.parallel(f"Making {len(commands)} wav files...", commands)
        sh.touch(tmp_dir.glob("*.wav"))
        for filename in sorted(tmp_dir.glob("*.wav"), key=text.alpha_numeric_key):
            subprocess.run(  # noqa: S603
                ("sndfile-convert", "-pcm16", filename, str(filename).replace("/__tmp__/", "/")),
                check=True,
            )
        shutil.rmtree(tmp_dir)
