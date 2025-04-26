"""Test AudioSource."""

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
from pathlib import Path
from unittest import TestCase

from audiolibrarian.audiosource import FilesAudioSource

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioSource(TestCase):
    """Test AudioSource."""

    def test__single_directory_argument(self) -> None:
        """Test single directory argument."""
        audio_source = FilesAudioSource([test_data_path])
        # This will need updated if more test files are added.
        self.assertEqual(7, len(audio_source.get_source_filenames()))
        self.assertListEqual([], audio_source.get_wav_filenames())
        audio_source.copy_wavs(Path("/tmp"))  # noqa: S108

    def test__front_cover(self) -> None:
        """Test front cover."""
        audio_source = FilesAudioSource([test_data_path / "09.flac"])
        front_cover = audio_source.get_front_cover()
        self.assertIsNotNone(front_cover)
        if front_cover:
            self.assertEqual("image/jpeg", front_cover.mime)
            self.assertIs(bytes, type(front_cover.data), "cover data should be of type: bytes")

    def test__get_search_data(self) -> None:
        """Test search data."""
        audio_source = FilesAudioSource([test_data_path / "00.mp3"])
        self.assertDictEqual({}, audio_source.get_search_data())

        audio_source = FilesAudioSource([test_data_path / "09.flac"])
        expected = {
            "mb_artist_id": "7364dea6-ca9a-48e3-be01-b44ad0d19897",
            "mb_release_id": "840b16e6-975f-4867-be37-ee48d771ec18",
        }
        self.assertDictEqual(expected, audio_source.get_search_data())

    def test__source_list(self) -> None:
        """Test source list."""
        audio_source = FilesAudioSource([test_data_path / "00.mp3"])
        self.assertListEqual([], audio_source.source_list)
        audio_source.prepare_source()  # This should run w/o helper programs on an empty list.

        audio_source = FilesAudioSource([test_data_path / "09.flac"])
        _ = audio_source.source_list
        source_list = audio_source.source_list  # Run twice to test stored value.
        self.assertEqual(9, len(source_list))
        for i in range(8):
            self.assertIsNone(source_list[i])
        self.assertIsNotNone(source_list[8])
