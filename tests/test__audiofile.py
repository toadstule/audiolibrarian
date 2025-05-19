"""Test AudioFile."""

#
#  Copyright (c) 2020 Stephen Jibson
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
import contextlib
import copy
import hashlib
import pathlib
import tempfile
from pathlib import Path
from typing import Any
from unittest import TestCase

from audiolibrarian.audiofile import audiofile
from audiolibrarian.records import (
    FrontCover,
    ListF,
    Medium,
    OneTrack,
    People,
    Performer,
    Release,
    Source,
    Track,
)

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioFile(TestCase):
    """Test AudioFile."""

    _blank_test_files = (p.resolve() for p in test_data_path.glob("00.*"))

    def setUp(self) -> None:
        """Set up the tests."""
        self.maxDiff = None
        self._verify_test_data()

    def tearDown(self) -> None:
        """Tear down the tests."""
        self._verify_test_data()

    def _verify_test_data(self) -> None:
        """Verify that our test data files haven't been modified.

        See test_data/README.md for more info.
        """
        with (test_data_path / "checksums").open() as checksum_file:
            for line in checksum_file:
                checksum, filename = line.strip().split()
                filepath = test_data_path / filename
                got = hashlib.md5(filepath.read_bytes()).hexdigest()  # noqa: S324
                self.assertEqual(checksum, got, f"Mismatched checksum for {filepath}")

    def test__no_changes_rw(self) -> None:
        """Verify that a read/write cycle doesn't change any tags."""
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                before = dict(f._mut_file.tags or {})  # noqa: SLF001
                f.write_tags()
                after = dict(f._mut_file.tags or {})  # noqa: SLF001

            # TIPL can be in any order, so we'll compare it separately and remove it.
            tipl_before, tipl_after = [], []
            if t := before.get("TIPL"):
                tipl_before = sorted(t.people)
                del before["TIPL"]
            if t := after.get("TIPL"):
                tipl_after = sorted(t.people)
                del after["TIPL"]
            self.assertListEqual(tipl_before, tipl_after, f"TIPL changed in {src}")
            self.assertDictEqual(before, after, f"Tags changed in {src}")

    def test__no_changes_wr_blank(self) -> None:
        """Verify that a write/read cycle doesn't change any blank tags."""
        blank_info = OneTrack()
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                f.one_track = blank_info
                f.write_tags()
                info = f.read_tags()
                self.assertEqual(blank_info, info, f"Blank file modified for {src.suffix}")
                self.assertTrue(f.__repr__().startswith("AudioFile: /"))

    def test__no_changes_wr(self) -> None:
        """Verify that a write/read cycle doesn't change any tags."""
        info = OneTrack(
            release=Release(
                album="Album",
                album_artists=ListF(["Album Artist One", "Album Artist Two"]),
                album_artists_sort=ListF(["One, Album Artist", "Two, Album Artist"]),
                asins=["ASIN 1", "ASIN 2"],
                barcodes=["Barcode 1", "Barcode 2"],
                catalog_numbers=["Catalog Number 1", "Catalog Number 2"],
                date="2015-09-24",
                front_cover=FrontCover(data=b"", desc="front", mime="image/jpg"),
                genres=ListF(["Genre 1", "Genre 2"]),
                labels=["Label 1", "Label 2"],
                media={
                    7: Medium(
                        formats=ListF(["Media 1 Format"]),
                        titles=["Disc title 1", "Disc title 2"],
                        track_count=10,
                        tracks={
                            3: Track(
                                artist="Track Artist",
                                artists=ListF(["Track Artist One", "Track Artist Two"]),
                                artists_sort=["One, Track Artist", "Two, Track Artist"],
                                isrcs=["ISRCS 1", "ISRCS 2"],
                                musicbrainz_artist_ids=ListF(["MB-Artist-ID-1", "MB-Artist-ID-2"]),
                                musicbrainz_release_track_id="MB-Release-Track-ID",
                                musicbrainz_track_id="MB-Track_ID",
                                title="Track Title",
                                track_number=3,
                            )
                        },
                    )
                },
                medium_count=14,
                musicbrainz_album_artist_ids=ListF(
                    ["MB-Album-Artist-ID-1", "MB-Album-Artist-ID-2"]
                ),
                musicbrainz_album_id="MB-Album-ID",
                musicbrainz_release_group_id="MB-Release-Group_ID",
                original_date="1972-04-02",
                original_year="1992",
                people=People(
                    engineers=["Engineer 1", "Engineer 2"],
                    lyricists=["Lyricist 1", "Lyricist 2"],
                    mixers=["Mixer 1", "Mixer 2"],
                    performers=[
                        Performer(name="Performer 1", instrument="Instrument 1"),
                        Performer(name="Performer 2", instrument="Instrument 2"),
                    ],
                    producers=["Producer 1", "Producer 2"],
                ),
                release_countries=["Release Country 1", "Release Country 2"],
                release_statuses=["Release Status 1", "Release Status 2"],
                release_types=["Release Type 1", "Release Type 2"],
                script="Script",
                source=Source.TAGS,
            ),
            medium_number=7,
            track_number=3,
        )
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                f._one_track = info  # noqa: SLF001
                f.write_tags()
                old_info = copy.deepcopy(info)
                new_info = f.read_tags()

                # Remove stuff we don't want to check.
                new_info.track.file_info = None

                if src.suffix == ".m4a":
                    old_info.release.people.performers = None  # m4a doesn't save performers.
                    old_info.release.front_cover.desc = None  # m4a doesn't save cover desc.
                if src.suffix == ".mp3":
                    old_info.release.original_date = None  # mp3 doesn't save orig date.
                self.assertEqual(old_info, new_info, f"Write/Read failed for {src.suffix}")


class TestAudioFileMisc(TestCase):
    """Test AudioFile miscellaneous functions."""

    def test__file_not_found(self) -> None:
        """Test file-not-found."""
        with self.assertRaises(FileNotFoundError):
            audiofile.AudioFile.open("your_mom_goes_to_college.mp3")

    def test__file_not_supported(self) -> None:
        """Test file-not-supported."""
        with self.assertRaises(NotImplementedError):
            # The current file should always be around, and never be an audio file.
            audiofile.AudioFile.open(__file__)


def _audio_file_copy(src_filepath: pathlib.Path) -> contextlib.closing[Any]:
    # Create a copy of the given source file and return the copy as a context-manager.
    #
    # We work with a temp copy of the file, so we don't break our test data.
    dst = tempfile.NamedTemporaryFile(mode="wb", prefix="test_", suffix=src_filepath.suffix)  # noqa: SIM115
    dst.write(src_filepath.read_bytes())
    dst.flush()
    dst.seek(0)
    return contextlib.closing(dst)
