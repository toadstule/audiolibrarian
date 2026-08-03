#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test AudioSource."""

from pathlib import Path
from typing import Final

import pytest

from audiolibrarian.audiosource import FilesAudioSource

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioSource:
    """Test AudioSource."""

    _TEST_FILE_COUNT: Final[int] = 7
    _TEST_TRACK_NUMBER: Final[int] = 9

    @pytest.fixture(scope="class")
    @classmethod
    def audio_source(cls) -> FilesAudioSource:
        """Return a FLAC audio source instance."""
        return FilesAudioSource([test_data_path / f"0{cls._TEST_TRACK_NUMBER}.flac"])

    @pytest.fixture(scope="class")
    @classmethod
    def blank_audio_source(cls) -> FilesAudioSource:
        """Return an MP3 audio source instance."""
        return FilesAudioSource([test_data_path / "00.mp3"])

    def test__single_directory_argument(self) -> None:
        """Test single directory argument."""
        audio_source = FilesAudioSource([test_data_path])
        # This will need updated if more test files are added.
        assert len(audio_source.get_source_filenames()) == self._TEST_FILE_COUNT
        assert audio_source.get_wav_filenames() == []
        audio_source.copy_wavs(Path("/tmp"))  # noqa: S108

    def test__front_cover(self, audio_source: FilesAudioSource) -> None:
        """Test front cover."""
        front_cover = audio_source.get_front_cover()
        assert front_cover is not None
        if front_cover:
            assert front_cover.mime == "image/jpeg"
            assert type(front_cover.data) is bytes, "cover data should be of type: bytes"

    def test__get_search_data(self, audio_source: FilesAudioSource, blank_audio_source: FilesAudioSource) -> None:
        """Test search data."""
        assert blank_audio_source.get_search_data() == {}

        expected = {
            "mb_artist_id": "7364dea6-ca9a-48e3-be01-b44ad0d19897",
            "mb_release_id": "840b16e6-975f-4867-be37-ee48d771ec18",
        }
        assert audio_source.get_search_data() == expected

    def test__source_list(self, audio_source: FilesAudioSource, blank_audio_source: FilesAudioSource) -> None:
        """Test source list."""
        assert blank_audio_source.source_list == []
        blank_audio_source.prepare_source()  # Should run w/o helper programs on an empty list.

        _ = audio_source.source_list
        source_list = audio_source.source_list  # Run twice to test stored value.
        assert len(source_list) == self._TEST_TRACK_NUMBER
        for i in range(self._TEST_TRACK_NUMBER - 1):
            assert source_list[i] is None
        assert source_list[self._TEST_TRACK_NUMBER - 1] is not None
