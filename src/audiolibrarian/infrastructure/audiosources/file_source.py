#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""AudioSource from local files."""

from __future__ import annotations

import logging
import shutil
import subprocess
from typing import TYPE_CHECKING

from audiolibrarian import audiofile, sh
from audiolibrarian.common import text
from audiolibrarian.infrastructure.audiosources._audiosource import AudioSource

if TYPE_CHECKING:
    import pathlib
    from collections.abc import Callable

    from audiolibrarian.domain.model import values


log = logging.getLogger(__name__)


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

    def get_front_cover(self) -> values.FrontCover | None:
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
                (
                    "/usr/bin/sndfile-convert",
                    "-pcm16",
                    filename,
                    str(filename).replace("/__tmp__/", "/"),
                ),
                check=True,
            )
        shutil.rmtree(tmp_dir)
