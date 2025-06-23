"""Test AudioLibrarian."""
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

from argparse import Namespace
from pathlib import Path
from typing import Final

import pytest

from audiolibrarian import base

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioLibrarian:
    """Test AudioLibrarian."""

    AUDIO_FILE_COUNT: Final[int] = 21  # This will need updated if test files are added.

    @pytest.fixture
    def al_base(self) -> base.Base:
        """Return a Base instance with a blank namespace."""
        return base.Base(args=Namespace())

    def test__single_media(self, al_base: base.Base) -> None:
        """Test single media."""
        assert not al_base._multi_disc
        assert al_base._flac_filenames == []
        assert al_base._m4a_filenames == []
        assert al_base._mp3_filenames == []
        assert al_base._source_filenames == []
        assert al_base._wav_filenames == []

        with pytest.warns(RuntimeWarning):
            al_base._convert()
        with pytest.warns(RuntimeWarning):
            al_base._summary()

    def test__multi_media(self) -> None:
        """Test multi-media."""
        al = base.Base(args=Namespace(disc="2/3"))

        assert al._multi_disc
        searcher = al._get_searcher()
        assert searcher.disc_number == "2"

    def test__find_audio_files(self, al_base: base.Base) -> None:
        """Test find-audio-files."""
        audio_files = list(al_base._find_audio_files([]))
        assert audio_files == []

        audio_files = list(al_base._find_audio_files([test_data_path]))
        assert len(audio_files) == self.AUDIO_FILE_COUNT

    def test__manifests(self, al_base: base.Base) -> None:
        """Test manifests."""
        manifests = list(al_base._find_manifests([]))
        assert manifests == []

        manifests = al_base._find_manifests([test_data_path])
        assert len(manifests) == 1
        assert al_base._manifest_file == manifests[0].name

        manifest = al_base._read_manifest(manifests[0])
        assert manifest.get("album") == "The Secret"

    @pytest.mark.parametrize(
        ("namespace", "expected"),
        [
            (Namespace(), ("", "", "", "", "", "")),
            (Namespace(artist="your mom"), ("your mom", "", "", "", "", "")),
            (
                Namespace(artist="your mom", album="the college years"),
                ("your mom", "the college years", "", "", "", ""),
            ),
            (
                Namespace(
                    artist="your mom",
                    album="the college years",
                    mb_artist_id="aid",
                    mb_release_id="rid",
                ),
                ("your mom", "the college years", "", "", "aid", "rid"),
            ),
        ],
    )
    def test__get_searcher(
        self, namespace: Namespace, expected: tuple[str, str, str, str, str, str]
    ) -> None:
        """Test searcher."""
        al_base = base.Base(args=namespace)
        searcher = al_base._get_searcher()
        assert (
            searcher.artist,
            searcher.album,
            searcher.disc_id,
            searcher.disc_mcn,
            searcher.mb_artist_id,
            searcher.mb_release_id,
        ) == expected
