#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Audio normalizer using wavegain."""

import logging
import pathlib
import shutil
import subprocess

from audiolibrarian import config
from audiolibrarian.infrastructure.normalizers.normalizer import Normalizer

log = logging.getLogger(__name__)


class WaveGainNormalizer(
    Normalizer[config.NormalizeWavegainSettings], priority=2, available=shutil.which("wavegain") is not None
):
    """Audio normalizer using wavegain."""

    name: str = "wavegain"

    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Normalize audio files using wavegain.

        Args:
            paths: List of audio file paths to normalize.

        Raises:
            subprocess.CalledProcessError: If wavegain process fails.
        """
        if not paths:
            return

        log.info("Normalizing %d files with wavegain...", len(paths))

        command = [
            "wavegain",
            f"--{self._settings.preset}",
            f"--gain={self._settings.gain}",
            "--apply",
            *[str(f) for f in paths],
        ]
        result = subprocess.run(command, capture_output=True, check=False)  # noqa: S603
        for line in str(result.stderr).split(r"\n"):
            line_trunc = line[:137] + "..." if len(line) > 140 else line  # noqa: PLR2004
            log.info("WAVEGAIN: %s", line_trunc)
        result.check_returncode()  # May raise subprocess.CalledProcessError.
