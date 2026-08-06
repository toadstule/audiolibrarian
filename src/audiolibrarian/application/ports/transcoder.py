#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for transcoders."""

import pathlib
from typing import Protocol, runtime_checkable

from audiolibrarian.domain.model import enums


@runtime_checkable
class TranscoderP(Protocol):
    """A transcoder port."""

    def transcode(
        self,
        input_path: pathlib.Path,
        output_path: pathlib.Path,
        *,
        input_format: enums.FileFormat | None = None,
        output_format: enums.FileFormat | None = None,
    ) -> None:
        """Transcode an audio file.

        Args:
            input_path: The path to the input file.
            output_path: The path to the output file.
            input_format: The input file format (optional; will be detected from the file extension, if None).
            output_format: The output file format (optional; will be detected from the file extension, if None).

        Raises:
            FileNotFoundError: If the input file is not found.
            TranscodeError: If the transcode fails.
        """
        ...
