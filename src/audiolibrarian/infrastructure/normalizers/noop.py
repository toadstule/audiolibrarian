#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""No-op normalizer."""

import logging
import pathlib

from audiolibrarian import config
from audiolibrarian.infrastructure.normalizers.normalizer import Normalizer

log = logging.getLogger(__name__)


class NoOpNormalizer(Normalizer[config.EmptySettings], priority=0, available=True):
    """No-op normalizer that does nothing."""

    name: str = "none"

    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Do not perform any normalization."""
        del paths  # Unused.
        log.info("Skipping audio normalization")
