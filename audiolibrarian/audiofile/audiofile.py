import abc
from pathlib import Path

import mutagen

from audiolibrarian.audiofile.audioinfo import Info


class AudioFile(abc.ABC):
    extensions = ()

    def __init__(self, filepath: Path):
        self._filepath = filepath
        self._mut_file = mutagen.File(self.filepath.absolute())
        self._info = self.read_tags()

    @property
    def filepath(self) -> Path:
        return self._filepath

    @property
    def info(self) -> Info:
        return self._info

    @info.setter
    def info(self, info: Info) -> None:
        self._info = info

    @abc.abstractmethod
    def read_tags(self) -> Info:
        pass

    @abc.abstractmethod
    def write_tags(self) -> None:
        pass
