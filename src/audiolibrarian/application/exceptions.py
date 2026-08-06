#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application layer exceptions."""

from audiolibrarian.domain.model import enums


class ApplicationError(Exception):
    """Base exception for application layer errors."""


class NormalizerError(ApplicationError):
    """Base exception for normalizer-related errors."""


class TranscodeError(ApplicationError):
    """Base exception for transcoder-related errors."""


class UnsupportedFileFormatError(TranscodeError):
    """Exception raised when a format is not supported by a transcoder."""

    def __init__(self, file_format: enums.FileFormat) -> None:
        """Initialize an UnsupportedFileFormatError."""
        self.file_format = file_format
        super().__init__(f"Unsupported file format: {file_format}")
