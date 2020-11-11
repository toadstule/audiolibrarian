import re
from argparse import ArgumentParser, Namespace
from logging import getLogger
from pathlib import Path

from audiolibrarian import __version__
from audiolibrarian.audiofile import open_
from audiolibrarian.audiosource import CDAudioSource, FilesAudioSource
from audiolibrarian.base import Base
from audiolibrarian.genremanager import GenreManager

log = getLogger(__name__)


class _Command:
    # Base class for commands.
    help = ""
    parser = ArgumentParser()

    @staticmethod
    def validate_args(args: Namespace) -> bool:
        _ = args
        return True


class Convert(_Command, Base):
    """AudioLibrarian tool for converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "convert"
    help = "convert music from files"
    parser = ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist (ignore tags)")
    parser.add_argument("--album", "-m", help="provide album (ignore tags)")
    parser.add_argument("--mb-artist-id", help="Musicbrainz artist ID")
    parser.add_argument("--mb-release-id", help="Musicbrainz release ID")
    parser.add_argument("--disc", "-d", help="format: x/y: disc x of y for multi-disc release")
    parser.add_argument("filename", nargs="+", help="directory name or audio file name")

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._source_is_cd = False
        self._audio_source = FilesAudioSource([Path(x) for x in args.filename])
        self._get_tag_info()
        self._convert()
        self._write_manifest()

    @staticmethod
    def validate_args(args: Namespace) -> bool:
        return _validate_disc_arg(args)


class Genre(_Command):
    """Do stuff with genres."""

    command = "genre"
    help = "manager MB genre"
    parser = ArgumentParser(
        description=(
            "Process all audio files in the given directory(ies), allowing the user to *update* "
            "the genre in Musicbrainz or *tag* audio files with the user-defined genre in "
            "Musicbrainz."
        )
    )
    parser.add_argument("directory", nargs="+", help="root of directory tree to process")
    parser_action = parser.add_mutually_exclusive_group()
    parser_action.add_argument("--tag", action="store_true", help="update tags")
    parser_action.add_argument("--update", action="store_true", help="update Musicbrainz")

    def __init__(self, args: Namespace) -> None:
        GenreManager(args)


class Manifest(_Command, Base):
    """AudioLibrarian tool for writing manifest.yaml files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "manifest"
    help = "create the Manifest.yaml file"
    parser = ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist (ignore tags)")
    parser.add_argument("--album", "-m", help="provide album (ignore tags)")
    parser.add_argument("--cd", "-c", action="store_true", help="original source was a CD")
    parser.add_argument("--mb-artist-id", help="Musicbrainz artist ID")
    parser.add_argument("--mb-release-id", help="Musicbrainz release ID")
    parser.add_argument("--disc", "-d", help="format: x/y: disc x of y for multi-disc release")
    parser.add_argument("filename", nargs="+", help="directory name or audio file name")

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._source_is_cd = args.cd
        self._audio_source = FilesAudioSource([Path(x) for x in args.filename])
        source_filenames = self._audio_source.get_source_filenames()
        self._source_example = open_(source_filenames[0]).read_tags()
        self._get_tag_info()
        self._write_manifest()

    @staticmethod
    def validate_args(args: Namespace) -> bool:
        return _validate_disc_arg(args)


class Reconvert(_Command, Base):
    """AudioLibrarian tool for re-converting and tagging audio files from existing source files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "reconvert"
    help = "re-convert files from an existing source directory"
    parser = ArgumentParser()
    parser.add_argument("directories", nargs="+", help="source directories")

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._source_is_cd = False
        for manifest_path in self._find_manifests(args.directories):
            print(f"Processing {manifest_path}...")
            self._audio_source = FilesAudioSource([manifest_path.parent])
            manifest = self._read_manifest(manifest_path)
            self._disc_number, self._disc_count = manifest["disc_number"], manifest["disc_count"]
            self._get_tag_info()
            self._convert(make_source=False)

    @staticmethod
    def validate_args(args: Namespace) -> bool:
        for directory in args.directories:
            if not Path(directory).is_dir():
                print(f"Directory not found: {directory}")
                return False
        return True


class Rip(_Command, Base):
    """AudioLibrarian tool for ripping, converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "rip"
    help = "rip music from a CD"
    parser = ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist")
    parser.add_argument("--album", "-m", help="provide album")
    parser.add_argument("--mb-artist-id", help="Musicbrainz artist ID")
    parser.add_argument("--mb-release-id", help="Musicbrainz release ID")
    parser.add_argument("--disc", "-d", help="x/y: disc x of y; multi-disc release")

    def __init__(self, args: Namespace) -> None:
        super().__init__(args)
        self._source_is_cd = True
        self._audio_source = CDAudioSource()
        self._get_tag_info()
        self._convert()
        self._write_manifest()

    @staticmethod
    def validate_args(args: Namespace) -> bool:
        return _validate_disc_arg(args)


class Version(_Command):
    """Print the version."""

    command = "version"
    help = "display the program version"

    def __init__(self, args: Namespace) -> None:
        _ = args
        print(f"audiolibrarian {__version__}")


def _validate_disc_arg(args: Namespace) -> bool:
    if "disc" in args and args.disc:
        if not re.match(r"\d+/\d+", args.disc):
            print("Invalid --disc specification; should be x/y")
            return False
    return True
