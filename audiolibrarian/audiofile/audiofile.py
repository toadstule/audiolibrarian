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


import abc
from pathlib import Path

import mutagen

from audiolibrarian.records import Medium, OneTrack, Release, Track


class AudioFile(abc.ABC):
    """Abstract base class for AudioFile classes."""

    extensions = ()

    def __init__(self, filepath: Path):
        self._filepath = filepath
        self._mut_file = mutagen.File(self.filepath.absolute())
        self._one_track = self.read_tags()

    def __repr__(self) -> str:
        return f"AudioFile: {self.filepath}"

    @property
    def filepath(self) -> Path:
        """Return the audio file's path."""
        return self._filepath

    @property
    def one_track(self) -> OneTrack:
        """Return the OneTrack representation of the audio file."""
        return self._one_track

    @one_track.setter
    def one_track(self, one_track: OneTrack) -> None:
        """Set the OneTrack representation of the audio file."""
        self._one_track = one_track

    @abc.abstractmethod
    def read_tags(self) -> OneTrack:
        """Reads the tags from the audio file and returns a populated OneTrack record."""

    @abc.abstractmethod
    def write_tags(self) -> None:
        """Write the tags to the audio file."""

    def _get_tag_sources(self) -> tuple[Release, int, Medium, int, Track]:
        # Return the objects and information required to generate tags.
        release = self.one_track.release or Release()
        medium_number = self.one_track.medium_number
        medium = self.one_track.medium or Medium()
        track_number = self.one_track.track_number
        track = self.one_track.track or Track()
        return release, medium_number, medium, track_number, track
