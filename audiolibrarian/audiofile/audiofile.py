import abc
from pathlib import Path
from typing import Tuple

import mutagen

from audiolibrarian.records import Medium, OneTrack, Release, Track


class AudioFile(abc.ABC):
    extensions = ()

    def __init__(self, filepath: Path):
        self._filepath = filepath
        self._mut_file = mutagen.File(self.filepath.absolute())
        self._one_track = self.read_tags()

    @property
    def filepath(self) -> Path:
        return self._filepath

    @property
    def one_track(self) -> OneTrack:
        return self._one_track

    @one_track.setter
    def one_track(self, one_track: OneTrack) -> None:
        self._one_track = one_track

    @abc.abstractmethod
    def read_tags(self) -> OneTrack:
        pass

    @abc.abstractmethod
    def write_tags(self) -> None:
        pass

    def _get_tag_sources(self) -> Tuple[Release, int, Medium, int, Track]:
        release = self.one_track.release or Release()
        medium_number = self.one_track.medium_number
        medium = self.one_track.medium or Medium()
        track_number = self.one_track.track_number
        track = self.one_track.track or Track()
        return release, medium_number, medium, track_number, track
