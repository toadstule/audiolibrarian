#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""AudioSource."""

from __future__ import annotations

import abc
import logging
import pathlib
import shutil
import tempfile

from audiolibrarian.common import text
from audiolibrarian.domain.model import values

log = logging.getLogger(__name__)


class AudioSource(abc.ABC):
    """An abstract base class for AudioSource classes."""

    def __init__(self) -> None:
        """Initialize an AudioSource."""
        self._temp_dir: pathlib.Path = pathlib.Path(tempfile.mkdtemp())
        self._source_list: list[pathlib.Path | None] = []

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
            length = max(self._get_track_number(str(f.name)).value for f in source_filenames)
            result: list[pathlib.Path | None] = [None] * length
            if length:
                for filename in source_filenames:
                    idx = self._get_track_number(str(filename.name)).value - 1
                    result[idx] = filename
            self._source_list = result
        return self._source_list

    def copy_wavs(self, dest_dir: pathlib.Path) -> None:
        """Copy wav files to the given destination directory."""
        for filename in self.get_wav_filenames():
            shutil.copy2(filename, dest_dir / filename.name)

    def get_front_cover(self) -> values.FrontCover | None:
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

    @staticmethod
    def _get_track_number(filename: str) -> values.TrackNumber:
        """Return the track number from a filename or user input."""
        if numbers := text.get_numbers(filename):
            return values.TrackNumber(value=int(numbers[0]))
        return values.TrackNumber.from_user_input(f"Enter the track number for: {filename}")
