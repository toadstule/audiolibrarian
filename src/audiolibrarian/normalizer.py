"""Audio normalization functionality using different backends."""
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
#  You should have received a copy of the GNU General Public License along with audiolibrarian.`
#  If not, see <https://www.gnu.org/licenses/>.
#

import abc
import logging
import pathlib
import shutil
import subprocess
from typing import Any, TypeVar

import ffmpeg_normalize
import pydantic

from audiolibrarian import config

log = logging.getLogger(__name__)

T = TypeVar("T", bound=pydantic.BaseModel)


class Normalizer[T](abc.ABC):
    """Abstract base class for audio normalizers."""

    def __init__(self, settings: T) -> None:
        """Initialize a Normalizer instance.

        Args:
            settings: The settings specific to this normalizer type.
        """
        self._settings: T = settings

    @classmethod
    def factory(cls, settings: config.NormalizeSettings) -> "Normalizer[Any]":
        """Create the appropriate normalizer based on settings.

        Args:
            settings: The normalization settings.

        Returns:
            An instance of the appropriate Normalizer implementation.
        """
        if settings.normalizer == "none":
            return NoOpNormalizer(config.EmptySettings())

        wavegain_found = shutil.which("wavegain")
        if settings.normalizer in ("auto", "wavegain") and wavegain_found:
            return WaveGainNormalizer(settings.wavegain)

        ffmpeg_found = shutil.which("ffmpeg")
        if settings.normalizer in ("auto", "ffmpeg") and ffmpeg_found:
            return FFmpegNormalizer(settings.ffmpeg)

        if wavegain_found:
            log.warning("ffmpeg not found, using wavegain for normalization")
            return WaveGainNormalizer(settings.wavegain)
        if ffmpeg_found:
            log.warning("wavegain not found, using ffmpeg for normalization")
            return FFmpegNormalizer(settings.ffmpeg)
        log.warning("wavegain not found, ffmpeg not found, using no normalization")
        return NoOpNormalizer(config.EmptySettings())

    @abc.abstractmethod
    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Normalize the given audio files.

        Args:
            paths: Set of audio file paths to normalize.

        Raises:
            Exception: If the normalization process fails.
        """


class NoOpNormalizer(Normalizer[config.EmptySettings]):
    """No-op normalizer that does nothing."""

    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Do not perform any normalization."""
        del paths  # Unused.
        log.info("Skipping audio normalization")


class WaveGainNormalizer(Normalizer[config.NormalizeWavegainSettings]):
    """Audio normalizer using wavegain."""

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


class FFmpegNormalizer(Normalizer[config.NormalizeFFmpegSettings]):
    """Audio normalizer using ffmpeg-normalize."""

    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Normalize audio files using ffmpeg-normalize.

        Args:
            paths: List of audio file paths to normalize.

        Raises:
            Exception: If ffmpeg-normalize process fails.
        """
        if not paths:
            return

        log.info("Normalizing %d files with ffmpeg-normalize...", len(paths))

        normalizer = ffmpeg_normalize.FFmpegNormalize(
            extension="wav",
            keep_loudness_range_target=True,
            target_level=self._settings.target_level,
        )
        for path in paths:
            normalizer.add_media_file(str(path), str(path))
        log.info("Starting ffmpeg normalization...")
        normalizer.run_normalization()
        log.info("FFmpeg normalization completed successfully")
