#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Audio normalizer using ffmpeg-normalize."""

import logging
import pathlib
import shutil

import ffmpeg_normalize

from audiolibrarian import config
from audiolibrarian.infrastructure.normalizers._normalizer import Normalizer

log = logging.getLogger(__name__)


class FFmpegNormalizer(
    Normalizer[config.NormalizeFFmpegSettings], priority=1, available=shutil.which("ffmpeg") is not None
):
    """Audio normalizer using ffmpeg-normalize."""

    name: str = "ffmpeg"

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
            audio_codec="pcm_s16le",
            extension="wav",
            extra_output_options=["-ar:a", "44100"],
            keep_loudness_range_target=True,
            target_level=self._settings.target_level,
        )
        for path in paths:
            normalizer.add_media_file(str(path), str(path))
        log.info("Starting ffmpeg normalization...")
        normalizer.run_normalization()
        log.info("FFmpeg normalization completed successfully")
