import pathlib

from audiolibrarian.audiofile.flac import FlacFile
from audiolibrarian.audiofile.m4a import M4aFile
from audiolibrarian.audiofile.mp3 import Mp3File
from audiolibrarian.audiofile.wav import WavFile

_formats = [
    FlacFile,
    M4aFile,
    Mp3File,
    WavFile,
]


def open_(filename: str) -> (str, None):
    """Factory function that returns an AudioFile object based on the filename extension."""
    filepath = pathlib.Path(filename)
    for fmt in _formats:
        if filepath.suffix in fmt.extensions:
            return fmt(filepath=filepath)
    print(f"Unknown file type: {filepath}")
