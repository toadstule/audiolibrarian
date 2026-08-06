#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""AudioSource from a compact disc."""

from __future__ import annotations

import logging
import os
import pathlib
import subprocess
from typing import TYPE_CHECKING

import discid

from audiolibrarian.infrastructure.audiosources._audiosource import AudioSource

if TYPE_CHECKING:
    from audiolibrarian import config

log = logging.getLogger(__name__)


class CDAudioSource(AudioSource):
    """AudioSource from a compact disc."""

    def __init__(self, settings: config.Settings) -> None:
        """Initialize a CDAudioSource."""
        super().__init__()
        self._cd = discid.read(settings.discid_device or None, features=["mcn"])

    def get_search_data(self) -> dict[str, str]:
        """Return a dictionary of search data useful for doing a MusicBrainz search."""
        result = {"disc_id": self._cd.id}
        if self._cd.mcn is not None:
            result["disc_mcn"] = self._cd.mcn
        return result

    def get_source_filenames(self) -> list[pathlib.Path]:
        """Return a list of the original source file paths.

        Since we're working with a CD, these files may not yet exist if they have not been
        read from the disc.
        """
        return [self._temp_dir / f"track{str(n + 1).zfill(2)}.cdda.wav" for n in range(self._cd.last_track_num)]

    def prepare_source(self) -> None:
        """Pull audio from the CD to wav files."""
        cwd = pathlib.Path.cwd()
        os.chdir(self._temp_dir)
        try:
            subprocess.run(("/usr/bin/cd-paranoia", "-B"), check=True)
        finally:
            os.chdir(cwd)
        subprocess.run(("/usr/bin/eject",), check=False)
