#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Audio file library."""

import abc
import importlib
import pathlib
from typing import Any, ClassVar

import mutagen

from audiolibrarian.domain.model import release, values
from audiolibrarian.domain.model.medium import Medium
from audiolibrarian.domain.model.release import Release
from audiolibrarian.domain.model.track import Track


class TagGateway(abc.ABC):
    """Abstract base class for TagGateway classes."""

    _subclass_by_extension: ClassVar[dict[str, type["TagGateway"]]] = {}

    def __init__(self, filepath: pathlib.Path) -> None:
        """Initialize an TagGateway."""
        self._filepath = filepath
        self._mut_file = mutagen.File(self.filepath.absolute())
        self._one_track = self.read_tags()

    def __init_subclass__(cls, extensions: set[str], **kwargs: dict[str, Any]) -> None:
        """Initialize an TagGateway subclass."""
        super().__init_subclass__(**kwargs)
        for extension in extensions:
            cls._subclass_by_extension[extension] = cls

    def __repr__(self) -> str:
        """Return a string representation of the TagGateway."""
        return f"TagGateway: {self.filepath}"

    @classmethod
    def extensions(cls) -> set[str]:
        """Return the list of supported extensions."""
        return set(cls._subclass_by_extension.keys())

    @classmethod
    def factory(cls, filename: str | pathlib.Path) -> "TagGateway":
        """Return an TagGateway object based on the filename extension (factory method).

        Args:
            filename: The filename of a supported audio file.

        Returns:
            audiofile.TagGateway: An TagGateway object.

        Raises:
            FileNotFoundError: If the file cannot be found or is not a file.
            NotImplementedError: If the type of the file is not supported.
        """
        if not TagGateway._subclass_by_extension:
            # Dynamically load submodules.
            for module_path in (pathlib.Path(__file__).parent / "formats").glob("*.py"):
                if module_path.name == "__init__.py":
                    continue
                importlib.import_module(f"audiolibrarian.audiofile.formats.{module_path.stem}")

        filepath = pathlib.Path(filename).resolve()
        if not filepath.is_file():
            raise FileNotFoundError(filepath)
        if filepath.suffix not in TagGateway._subclass_by_extension:
            msg = f"Unknown file type: {filepath}"
            raise NotImplementedError(msg)
        return TagGateway._subclass_by_extension[filepath.suffix](filepath=filepath)

    @property
    def filepath(self) -> pathlib.Path:
        """Return the audio file's path."""
        return self._filepath

    @property
    def one_track(self) -> release.OneTrack:
        """Return the OneTrack representation of the audio file."""
        return self._one_track

    @one_track.setter
    def one_track(self, one_track: release.OneTrack) -> None:
        """Set the OneTrack representation of the audio file."""
        self._one_track = one_track

    @abc.abstractmethod
    def read_tags(self) -> release.OneTrack:
        """Read the tags from the audio file and return a populated OneTrack record."""

    @abc.abstractmethod
    def write_tags(self) -> None:
        """Write the tags to the audio file."""

    def _get_tag_sources(self) -> tuple[Release, int | None, Medium, values.TrackNumber | None, Track]:
        # Return the objects and information required to generate tags.
        release_ = self.one_track.release or Release()
        medium_number = self.one_track.medium_position.number if self.one_track.medium_position else None
        medium = self.one_track.medium or Medium()
        track_number = self.one_track.track_number or None
        track = self.one_track.track or Track()
        return release_, medium_number, medium, track_number, track
