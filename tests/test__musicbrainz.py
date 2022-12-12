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
import logging
import os
from pathlib import Path
from unittest import TestCase, skipUnless

from audiolibrarian.audiofile import open_
from audiolibrarian.musicbrainz import MusicBrainzRelease
from audiolibrarian.records import Source
from tests.test__audiofile import _audio_file_copy

test_data_path = (Path(__file__).parent / "test_data").resolve()
if log_level := os.getenv("LOG_LEVEL"):
    logging.basicConfig(level=log_level)


class TestMusicBrainzRelease(TestCase):
    maxDiff = None
    _blank_test_files = [p.resolve() for p in test_data_path.glob("00.*")]

    @skipUnless(os.getenv("EXTERNAL_TESTS"), "EXTERNAL_TESTS not defined")
    def test__musicbrainz_release(self) -> None:
        """Verify that data we pull from MB service matches data from a picard-generated file."""
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = open_(test_file.name)  # mypy: ignore-errors  # type: ignore
                if (expected := f._one_track.release) is None:  # Blank tags in audio file.
                    continue
                medium_number = f._one_track.medium_number
                track_number = f._one_track.track_number

            got = MusicBrainzRelease(expected.musicbrainz_album_id).get_release()

            # Remove stuff we don't want to compare.
            expected.genres, got.genres = None, None  # Genres should be ignored.
            expected.front_cover, got.front_cover = None, None  # Don't compare image.
            expected.asins, got.asins = None, None  # Something's weird with ASINS.
            # noinspection PyUnresolvedReferences
            expected.media[medium_number].tracks[track_number].file_info = None
            # noinspection PyUnresolvedReferences
            got.media[medium_number].tracks[track_number].file_info = None

            if src.suffix == ".m4a":  # We don't store this for m4a files.
                if got.people:
                    got.people.performers = None

            if src.suffix == ".mp3":  # We don't store this for mp3 files.
                expected.original_date, got.original_date = None, None

            self.assertEqual(expected.people, got.people, f"People failed for {src}")
            expected.people, got.people = None, None

            # noinspection PyUnresolvedReferences
            self.assertEqual(
                expected.media[medium_number].tracks[track_number],
                got.media[medium_number].tracks[track_number],
                f"Track failed for {src}",
            )
            # noinspection PyUnresolvedReferences
            expected.media[medium_number].tracks, got.media[medium_number].tracks = None, None

            # noinspection PyUnresolvedReferences
            self.assertEqual(
                expected.media[medium_number],
                got.media[medium_number],
                f"Medium failed for {src}",
            )
            expected.media, got.media = None, None

            self.assertEqual(Source.TAGS, expected.source, f"Bad source from file read {src}")
            self.assertEqual(Source.MUSICBRAINZ, got.source, f"Bad source from musicbrainz {src}")
            expected.source, got.source = None, None

            self.assertEqual(expected, got, f"Failed for {src}")
