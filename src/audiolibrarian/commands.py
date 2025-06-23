"""Command line commands."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
import argparse
import logging
import pathlib
import re
from typing import Any

from audiolibrarian import __version__, audiofile, audiosource, base, genremanager

log = logging.getLogger(__name__)


class _Command:
    # Base class for commands.
    help = ""
    parser = argparse.ArgumentParser()

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        _ = args
        return True


class Convert(_Command, base.Base):
    """AudioLibrarian tool for converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "convert"
    help = "convert music from files"
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist (ignore tags)")
    parser.add_argument("--album", "-m", help="provide album (ignore tags)")
    parser.add_argument("--mb-artist-id", help="MusicBrainz artist ID")
    parser.add_argument("--mb-release-id", help="MusicBrainz release ID")
    parser.add_argument("--disc", "-d", help="format: x/y: disc x of y for multi-disc release")
    parser.add_argument("filename", nargs="+", help="directory name or audio file name")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Convert command handler."""
        super().__init__(args)
        self._source_is_cd = False
        self._audio_source = audiosource.FilesAudioSource([pathlib.Path(x) for x in args.filename])
        self._get_tag_info()
        self._convert()
        self._write_manifest()

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        return _validate_disc_arg(args)


class Genre(_Command):
    """Do stuff with genres."""

    command = "genre"
    help = "manage MB genre"
    parser = argparse.ArgumentParser(
        description=(
            "Process all audio files in the given directory(ies), allowing the user to *update* "
            "the genre in MusicBrainz or *tag* audio files with the user-defined genre in "
            "MusicBrainz."
        )
    )
    parser.add_argument("directory", nargs="+", help="root of directory tree to process")
    parser_action = parser.add_mutually_exclusive_group()
    parser_action.add_argument("--tag", action="store_true", help="update tags")
    parser_action.add_argument("--update", action="store_true", help="update MusicBrainz")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Genre command handler."""
        genremanager.GenreManager(args)


class Manifest(_Command, base.Base):
    """AudioLibrarian tool for writing manifest.yaml files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "manifest"
    help = "create the Manifest.yaml file"
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist (ignore tags)")
    parser.add_argument("--album", "-m", help="provide album (ignore tags)")
    parser.add_argument("--cd", "-c", action="store_true", help="original source was a CD")
    parser.add_argument("--mb-artist-id", help="MusicBrainz artist ID")
    parser.add_argument("--mb-release-id", help="MusicBrainz release ID")
    parser.add_argument("--disc", "-d", help="format: x/y: disc x of y for multi-disc release")
    parser.add_argument("filename", nargs="+", help="directory name or audio file name")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Manifest command handler."""
        super().__init__(args)
        self._source_is_cd = args.cd
        self._audio_source = audiosource.FilesAudioSource([pathlib.Path(x) for x in args.filename])
        source_filenames = self._audio_source.get_source_filenames()
        self._source_example = audiofile.AudioFile.open(source_filenames[0]).read_tags()
        self._get_tag_info()
        self._write_manifest()

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        return _validate_disc_arg(args)


class Reconvert(_Command, base.Base):
    """AudioLibrarian tool for re-converting and tagging audio files from existing source files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "reconvert"
    help = "re-convert files from an existing source directory"
    parser = argparse.ArgumentParser()
    parser.add_argument("directories", nargs="+", help="source directories")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Reconvert command handler."""
        super().__init__(args)
        self._source_is_cd = False
        manifest_paths = self._find_manifests(args.directories)
        count = len(manifest_paths)
        for i, manifest_path in enumerate(manifest_paths):
            print(f"Processing {i + 1} of {count} ({i / count:.0%}): {manifest_path}...")
            self._audio_source = audiosource.FilesAudioSource([manifest_path.parent])
            manifest = self._read_manifest(manifest_path)
            self._disc_number, self._disc_count = manifest["disc_number"], manifest["disc_count"]
            self._get_tag_info()
            self._convert(make_source=False)

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        return _validate_directories_arg(args)


class Rename(_Command, base.Base):
    """AudioLibrarian tool for renaming audio files based on their tags.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "rename"
    help = "rename files based on tags or MusicBrainz data"
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="don't actually rename files")
    parser.add_argument("directories", nargs="+", help="audio file directories")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Rename command handler."""
        super().__init__(args)
        self._source_is_cd = False
        print("Finding audio files...")
        for audio_file in self._find_audio_files(args.directories):
            filepath = audio_file.filepath
            if audio_file.one_track.track is None:
                log.warning("%s has no title", filepath)
                continue
            depth = 3 if filepath.parent.name.startswith("disc") else 2
            old_name = filepath
            new_name = (
                filepath.parents[depth]
                / audio_file.one_track.get_artist_album_disc_path()
                / audio_file.one_track.track.get_filename(filepath.suffix)
            )
            if old_name != new_name:
                print(f"Renaming:\n  {old_name} -> \n  {new_name}")
                if args.dry_run:
                    continue
                old_parent = old_name.parent
                new_parent = new_name.parent
                new_parent.mkdir(parents=True, exist_ok=True)
                old_name.rename(new_name)
                if not old_parent.samefile(new_parent):
                    # Move the Manifest if it's the only file left.
                    man = "Manifest.yaml"
                    if [f.name for f in old_parent.glob("*")] == [man]:
                        print(f"Renaming:\n  {old_parent / man} -> \n  {new_parent / man}")
                        (old_parent / man).rename(new_parent / man)
                    for idx in range(depth):
                        if not list(old_name.parents[idx].glob("*")):
                            print(f"Removing: {old_name.parents[idx]}")
                            old_name.parents[idx].rmdir()

            else:
                log.debug("Not renaming %s", filepath)

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        return _validate_directories_arg(args)


class Rip(_Command, base.Base):
    """AudioLibrarian tool for ripping, converting and tagging audio files.

    This class performs all of its tasks on instantiation and provides no public members or
    methods.
    """

    command = "rip"
    help = "rip music from a CD"
    parser = argparse.ArgumentParser()
    parser.add_argument("--artist", "-a", help="provide artist")
    parser.add_argument("--album", "-m", help="provide album")
    parser.add_argument("--mb-artist-id", help="MusicBrainz artist ID")
    parser.add_argument("--mb-release-id", help="MusicBrainz release ID")
    parser.add_argument("--disc", "-d", help="x/y: disc x of y; multi-disc release")

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Rip command handler."""
        super().__init__(args)
        self._source_is_cd = True
        self._audio_source = audiosource.CDAudioSource()
        self._get_tag_info()
        self._convert()
        self._write_manifest()

    @staticmethod
    def validate_args(args: argparse.Namespace) -> bool:
        """Validate command line arguments."""
        return _validate_disc_arg(args)


class Version(_Command):
    """Print the version."""

    command = "version"
    help = "display the program version"

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize a Version command handler."""
        _ = args
        print(f"audiolibrarian {__version__}")


def _validate_directories_arg(args: argparse.Namespace) -> bool:
    for directory in args.directories:
        if not pathlib.Path(directory).is_dir():
            print(f"Directory not found: {directory}")
            return False
    return True


def _validate_disc_arg(args: argparse.Namespace) -> bool:
    if "disc" in args and args.disc:
        if not re.match(r"\d+/\d+", args.disc):
            print("Invalid --disc specification; should be 'x/y'")
            return False
        x, y = args.disc.split("/")
        if int(x) > int(y) or int(x) < 1 or int(y) < 1:
            print("Invalid --disc specification; should be 'x/y' where x <= y and x and y  >= 1")
            return False
    return True


COMMANDS: set[Any] = {Convert, Genre, Manifest, Reconvert, Rename, Rip, Version}
