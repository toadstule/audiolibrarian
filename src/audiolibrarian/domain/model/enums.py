#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain model: enums."""

import enum


class BitrateMode(enum.Enum):
    """Bitrate modes."""

    UNKNOWN = 0
    CBR = 1
    VBR = 2


class FileType(enum.Enum):
    """Audio file types."""

    UNKNOWN = 0
    AAC = 1
    FLAC = 2
    MP3 = 3
    WAV = 4


class Source(enum.Enum):
    """Information source."""

    MUSICBRAINZ = 1
    TAGS = 2
