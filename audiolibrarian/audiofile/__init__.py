"""Audio file library."""
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
import pathlib
from typing import Any

from audiolibrarian.audiofile import audiofile, flac, m4a, mp3
from audiolibrarian.audiofile.audiofile import AudioFile

_AUDIOFILE_CLS_BY_EXTENSION: dict[str, Any] = {
    extension: audiofile_cls
    for audiofile_cls in [flac.FlacFile, m4a.M4aFile, mp3.Mp3File]
    for extension in audiofile_cls.extensions
}
EXTENSIONS: set[str] = set(_AUDIOFILE_CLS_BY_EXTENSION)


def open_(filename: str | pathlib.Path) -> audiofile.AudioFile:
    """Return an AudioFile object based on the filename extension (factory function).

    Args:
        filename: The filename of a supported audio file.

    Returns:
        audiofile.AudioFile: An AudioFile object.

    Raises:
        FileNotFoundError: If the file cannot be found or is not a file.
        NotImplementedError: If the type of the file is not supported.
    """
    filepath = pathlib.Path(filename).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(filepath)
    if filepath.suffix not in EXTENSIONS:
        raise NotImplementedError(f"Unknown file type: {filepath}")
    return _AUDIOFILE_CLS_BY_EXTENSION[filepath.suffix](filepath=filepath)  # type: ignore
