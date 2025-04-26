"""Test AudioLibrarian."""

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
from argparse import Namespace
from pathlib import Path
from unittest import TestCase

from audiolibrarian.base import Base

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioLibrarian(TestCase):
    """Test AudioLibrarian."""

    _blank_test_files = (p.resolve() for p in test_data_path.glob("00.*"))

    def test__single_media(self) -> None:
        """Test single media."""
        al = Base(args=Namespace())

        self.assertFalse(al._multi_disc)  # noqa: SLF001

        self.assertListEqual([], al._flac_filenames)  # noqa: SLF001
        self.assertListEqual([], al._m4a_filenames)  # noqa: SLF001
        self.assertListEqual([], al._mp3_filenames)  # noqa: SLF001
        self.assertListEqual([], al._source_filenames)  # noqa: SLF001
        self.assertListEqual([], al._wav_filenames)  # noqa: SLF001

        with self.assertWarns(RuntimeWarning):
            al._convert()  # noqa: SLF001
        with self.assertWarns(RuntimeWarning):
            al._summary()  # noqa: SLF001

    def test__multi_media(self) -> None:
        """Test multi-media."""
        al = Base(args=Namespace(disc="2/3"))

        self.assertTrue(al._multi_disc)  # noqa: SLF001
        searcher = al._get_searcher()  # noqa: SLF001
        self.assertEqual("2", searcher.disc_number)

    def test__find_audio_files(self) -> None:
        """Test find-audio-files."""
        al = Base(args=Namespace())
        audio_files = list(al._find_audio_files([]))  # noqa: SLF001
        self.assertEqual([], audio_files)

        audio_files = list(al._find_audio_files([test_data_path]))  # noqa: SLF001
        self.assertEqual(21, len(audio_files))  # This will need updated if test files are added.

    def test__manifests(self) -> None:
        """Test manifests."""
        al = Base(args=Namespace())
        manifests = list(al._find_manifests([]))  # noqa: SLF001
        self.assertEqual([], manifests)

        manifests = al._find_manifests([test_data_path])  # noqa: SLF001
        self.assertEqual(1, len(manifests))
        self.assertEqual(al._manifest_file, manifests[0].name)  # noqa: SLF001

        manifest = al._read_manifest(manifests[0])  # noqa: SLF001
        self.assertEqual("The Secret", manifest.get("album"))

    def test__get_searcher(self) -> None:
        """Test searcher."""
        al = Base(args=Namespace())
        searcher = al._get_searcher()  # noqa: SLF001
        self.assertEqual("", searcher.artist)
        self.assertEqual("", searcher.album)
        self.assertEqual("", searcher.disc_id)
        self.assertEqual("", searcher.disc_mcn)
        self.assertEqual("", searcher.mb_artist_id)
        self.assertEqual("", searcher.mb_release_id)

        al = Base(args=Namespace(artist="your mom"))
        searcher = al._get_searcher()  # noqa: SLF001
        self.assertEqual("your mom", searcher.artist)
        self.assertEqual("", searcher.album)
        self.assertEqual("", searcher.disc_id)
        self.assertEqual("", searcher.disc_mcn)
        self.assertEqual("", searcher.mb_artist_id)
        self.assertEqual("", searcher.mb_release_id)

        al = Base(
            args=Namespace(
                artist="your mom",
                album="the college years",
                mb_artist_id="aid",
                mb_release_id="rid",
            )
        )
        searcher = al._get_searcher()  # noqa: SLF001
        self.assertEqual("your mom", searcher.artist)
        self.assertEqual("the college years", searcher.album)
        self.assertEqual("", searcher.disc_id)
        self.assertEqual("", searcher.disc_mcn)
        self.assertEqual("aid", searcher.mb_artist_id)
        self.assertEqual("rid", searcher.mb_release_id)
