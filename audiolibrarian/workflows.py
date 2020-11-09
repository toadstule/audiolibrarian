from logging import getLogger
from pathlib import Path

from audiolibrarian.audiosource import CDAudioSource, FilesAudioSource
from audiolibrarian.base import Base


log = getLogger(__name__)


class Converter(Base):
    """AudioLibrarian tool for converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    def __init__(self, args):
        super().__init__(args)
        self._audio_source = FilesAudioSource([Path(x) for x in self._args.filename])
        self._get_tag_info()
        self._convert()
        self._write_manifest()


class Manifester(Base):
    """AudioLibrarian tool for writing manifest.yaml files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    def __init__(self, args):
        super().__init__(args)
        self._write_manifest()


class Ripper(Base):
    """AudioLibrarian tool for ripping, converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    def __init__(self, args):
        super().__init__(args)
        self._audio_source = CDAudioSource()
        self._get_tag_info()
        self._convert()
        self._write_manifest()
