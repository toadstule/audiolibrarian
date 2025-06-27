"""Test MusicBrainz."""

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
import logging
import os
from pathlib import Path

import pytest

from audiolibrarian import config
from audiolibrarian.audiofile import audiofile
from audiolibrarian.musicbrainz import MusicBrainzRelease
from audiolibrarian.records import Source
from tests.test__audiofile import _audio_file_copy

test_data_path = (Path(__file__).parent / "test_data").resolve()
if log_level := os.getenv("LOG_LEVEL"):
    logging.basicConfig(level=log_level)


class TestMusicBrainzRelease:
    """Test MusicBrainz."""

    maxDiff = None
    _blank_test_files = (p.resolve() for p in test_data_path.glob("00.*"))

    @pytest.fixture
    def settings(self) -> config.Settings:
        """Return a Settings instance."""
        return config.Settings()

    @pytest.mark.skipif(not os.getenv("EXTERNAL_TESTS"), reason="EXTERNAL_TESTS not defined")
    def test__musicbrainz_release(self, settings: config.Settings) -> None:
        """Verify that data we pull from MB service matches data from a picard-generated file."""
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                if (expected := f._one_track.release) is None:
                    # Blank tags in audio file.
                    continue
                medium_number = f._one_track.medium_number
                track_number = f._one_track.track_number

            got = MusicBrainzRelease(
                release_id=expected.musicbrainz_album_id,
                settings=settings.musicbrainz,
            ).get_release()

            # Remove stuff we don't want to compare.
            expected.genres, got.genres = None, None  # Genres should be ignored.
            expected.front_cover, got.front_cover = None, None  # Don't compare image.
            expected.asins, got.asins = None, None  # Something's weird with ASINS.
            if expected.people is not None:
                expected.people.engineers, got.people.engineers = None, None
                expected.people.lyricists, got.people.lyricists = None, None
                expected.people.mixers, got.people.mixers = None, None
                expected.people.producers, got.people.producers = None, None
            # noinspection PyUnresolvedReferences
            expected.media[medium_number].tracks[track_number].file_info = None
            # noinspection PyUnresolvedReferences
            got.media[medium_number].tracks[track_number].file_info = None

            if src.suffix == ".m4a" and got.people:  # We don't store this for m4a files.
                got.people.performers = None

            if src.suffix == ".mp3":  # We don't store this for mp3 files.
                expected.original_date, got.original_date = None, None

            assert got.people == expected.people, f"People failed for {src}"
            expected.people, got.people = None, None

            # noinspection PyUnresolvedReferences
            assert (
                got.media[medium_number].tracks[track_number]
                == expected.media[medium_number].tracks[track_number]
            ), f"Track failed for {src}"
            # noinspection PyUnresolvedReferences
            expected.media[medium_number].tracks, got.media[medium_number].tracks = None, None

            # noinspection PyUnresolvedReferences
            assert got.media[medium_number] == expected.media[medium_number], (
                f"Medium failed for {src}"
            )
            expected.media, got.media = None, None

            assert expected.source == Source.TAGS, f"Bad source from file read {src}"
            assert got.source == Source.MUSICBRAINZ, f"Bad source from musicbrainz {src}"
            expected.source, got.source = None, None

            assert got == expected, f"Failed for {src}"
