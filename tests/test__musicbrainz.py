from pathlib import Path
from unittest import TestCase

from audiolibrarian.audiofile import open_
from audiolibrarian.musicbrainz import MusicBrainzRelease
from audiolibrarian.records import Source
from tests.test__audiofile import _audio_file_copy

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestMusicBrainzRelease(TestCase):
    maxDiff = None
    _blank_test_files = [p.resolve() for p in test_data_path.glob("00.*")]

    def test__musicbrainz_release(self) -> None:
        """Verify that data we pull from MB service matches data from a picard-generated file."""
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = open_(test_file.name)
                if (expected := f._one_track.release) is None:  # Blank tags in audio file
                    continue
                medium_number = f._one_track.medium_number
                track_number = f._one_track.track_number

            got = MusicBrainzRelease(expected.musicbrainz_album_id).get_release()

            # remove stuff we don't want to compare
            expected.genres, got.genres = None, None  # genres should be ignored
            expected.front_cover, got.front_cover = None, None  # don't compare image
            expected.asins, got.asins = None, None  # Something's weird with ASINS

            if src.suffix == ".m4a":  # we don't store this for m4a files
                if got.people:
                    got.people.performers = None

            if src.suffix == ".mp3":  # we don't store this for mp3 files
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
