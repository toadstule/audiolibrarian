import abc
from pathlib import Path

import mutagen

from audiolibrarian.records import TrackView


class AudioFile(abc.ABC):
    extensions = ()

    def __init__(self, filepath: Path):
        self._filepath = filepath
        self._mut_file = mutagen.File(self.filepath.absolute())
        self._track_view = self.read_tags()

    @property
    def filepath(self) -> Path:
        return self._filepath

    @property
    def track_view(self) -> TrackView:
        return self._track_view

    @track_view.setter
    def track_view(self, track_view: TrackView) -> None:
        self._track_view = track_view

    @abc.abstractmethod
    def read_tags(self) -> TrackView:
        pass

    @abc.abstractmethod
    def write_tags(self) -> None:
        pass
