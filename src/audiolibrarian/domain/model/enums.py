#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: enums."""

import enum


class BitrateMode(enum.Enum):
    """Bitrate modes."""

    UNKNOWN = 0
    CBR = 1
    VBR = 2


class FileType(enum.StrEnum):
    """Audio file types."""

    UNKNOWN = "unknown"
    AAC = "mp4"
    FLAC = enum.auto()
    MP3 = enum.auto()
    WAV = enum.auto()


class Source(enum.Enum):
    """Information source."""

    MUSICBRAINZ = 1
    TAGS = 2
