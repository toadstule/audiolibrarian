#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for audio sources."""

import pathlib
from typing import Protocol, runtime_checkable

from audiolibrarian.domain.model import values


@runtime_checkable
class AudioSourceP(Protocol):
    """An audio source port."""

    source_list: list[pathlib.Path | None]

    def copy_wavs(self, dest_dir: pathlib.Path) -> None:
        """Copy wav files to the given destination directory."""
        ...

    def get_front_cover(self) -> values.FrontCover | None:
        """Return a FrontCover record or None."""
        ...

    def get_search_data(self) -> dict[str, str]:
        """Return a dictionary of search data useful for doing a MusicBrainz search."""
        ...

    def get_source_filenames(self) -> list[pathlib.Path]:
        """Return a list of the original source file paths."""
        ...

    def get_wav_filenames(self) -> list[pathlib.Path]:
        """Return a list of the prepared wav file paths."""
        ...

    def prepare_source(self) -> None:
        """Convert the source to wav files."""
        ...
