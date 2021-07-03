"""Base functions for the audio file library."""
#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

from pathlib import Path
from typing import Union

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.flac import FlacFile
from audiolibrarian.audiofile.m4a import M4aFile
from audiolibrarian.audiofile.mp3 import Mp3File

_audioFiles = [
    FlacFile,
    M4aFile,
    Mp3File,
]


def extensions() -> list[str]:
    """Return a sorted list of all filename extensions that can be opened by open_()."""
    ext = []
    for audioFile in _audioFiles:
        ext.extend(audioFile.extensions)
    return sorted(list(set(ext)))


def open_(filename: Union[str, Path]) -> AudioFile:
    """Return an AudioFile object based on the filename extension (factory function).

    Args:
        filename: The filename of a supported audio file.

    Returns:
        AudioFile: An AudioFile object.

    Raises:
        FileNotFoundError: If the file cannot be found or is not a file.
        NotImplementedError: If the type of the file is not supported.
    """
    filepath = Path(filename).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(filepath)
    for audioFile in _audioFiles:
        if filepath.suffix in audioFile.extensions:
            return audioFile(filepath=filepath)
    raise NotImplementedError(f"Unknown file type: {filepath}")
