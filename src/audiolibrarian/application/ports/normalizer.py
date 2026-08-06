#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for normalizers."""

import pathlib
from typing import Protocol, runtime_checkable


@runtime_checkable
class NormalizerP(Protocol):
    """A normalizer port."""

    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Normalize an audio file.

        Args:
            paths: A set of paths to normalize.

        Raises:
            FileNotFoundError: If a file is not found.
            NormalizerError: If the normalizer fails.
        """
        ...
