import pathlib

from audiolibrarian.audiofile.audiofile import AudioFile
from audiolibrarian.audiofile.flac import FlacFile
from audiolibrarian.audiofile.m4a import M4aFile
from audiolibrarian.audiofile.mp3 import Mp3File

_audioFiles = [
    FlacFile,
    M4aFile,
    Mp3File,
]


def open_(filename: str) -> AudioFile:
    """Factory function that returns an AudioFile object based on the filename extension.

    :param filename: filename of a supported audio file
    :return: an AudioFile object
    :raise FileNotFoundError: if the file cannot be found or is not a file
    :raise NotImplementedError: if the type of the file is not supported
    """

    filepath = pathlib.Path(filename).resolve()
    if not filepath.is_file():
        raise FileNotFoundError(filepath)
    for audioFile in _audioFiles:
        if filepath.suffix in audioFile.extensions:
            return audioFile(filepath=filepath)
    raise NotImplementedError(f"Unknown file type: {filepath}")
