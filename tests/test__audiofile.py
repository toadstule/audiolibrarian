import contextlib
import copy
import hashlib
import tempfile
from pathlib import Path
from unittest import TestCase

from audiolibrarian.audiofile import open_
from audiolibrarian.audioinfo import (
    Info,
    FrontCover,
    Performer,
    RelationInfo,
    ReleaseInfo,
    TrackInfo,
)

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestAudioFile(TestCase):
    _blank_test_files = [p.resolve() for p in test_data_path.glob("00.*")]

    def setUp(self) -> None:
        self.maxDiff = None
        self._verify_test_data()

    def tearDown(self) -> None:
        self._verify_test_data()

    def _verify_test_data(self) -> None:
        """Verify that our test data files haven't been modified.

        To update the checksums file, jump into the test_data directory and run:
        `rm checksums && md5sum * > checksums`
        """
        with (test_data_path / "checksums").open() as checksum_file:
            for line in checksum_file:
                checksum, filename = line.strip().split()
                filepath = test_data_path / filename
                got = hashlib.md5(filepath.read_bytes()).hexdigest()
                self.assertEqual(checksum, got, f"Mismatched checksum for {filepath}")

    def test__no_changes_rw(self) -> None:
        """Verify that a read/write cycle doesn't change any tags."""
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = open_(test_file.name)
                before = dict(f._mut_file.tags or {})
                f.write_tags()
                after = dict(f._mut_file.tags)

            # TIPL can be in any order, so we'll compare it separately and remove it
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
        blank_info = Info(
            relation_info=RelationInfo(), release_info=ReleaseInfo(), track_info=TrackInfo()
        )
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = open_(test_file.name)
                f._info = blank_info
                f.write_tags()
                info = f.read_tags()
                self.assertEqual(blank_info, info, f"Blank file modified for {src.suffix}")

    def test__no_changes_wr(self) -> None:
        """Verify that a write/read cycle doesn't change any tags."""

        info = Info(
            relation_info=RelationInfo(
                engineers=["Engineer 1", "Engineer 2"],
                lyricists=["Lyricist 1", "Lyricist 2"],
                mixers=["Mixer 1", "Mixer 2"],
                performers=[
                    Performer(name="Performer 1", instrument="Instrument 1"),
                    Performer(name="Performer 2", instrument="Instrument 2"),
                ],
                producers=["Producer 1", "Producer 2"],
            ),
            release_info=ReleaseInfo(
                album="Album",
                album_artists=["Album Artist One", "Album Artist Two"],
                album_artists_sort=["One, Album Artist", "Two, Album Artist"],
                asins=["ASIN 1", "ASIN 2"],
                barcodes=["Barcode 1", "Barcode 2"],
                catalog_numbers=["Catalog Number 1", "Catalog Number 2"],
                date="2015-09-24",
                disc_number=7,
                disc_total=14,
                front_cover=FrontCover(data=b"", desc="front", mime="image/jpg"),
                genres=["Genre 1", "Genre 2"],
                labels=["Label 1", "Label 2"],
                media=["Media 1", "Media 2"],
                musicbrainz_album_artist_ids=["MB-Album-Artist-ID-1", "MB-Album-Artist-ID-2"],
                musicbrainz_album_id="MB-Album-ID",
                musicbrainz_release_group_id="MB-Release-Group_ID",
                original_date="1972-04-02",
                original_year=1992,
                release_countries=["Release Country 1", "Release Country 2"],
                release_statuses=["Release Status 1", "Release Status 2"],
                release_types=["Release Type 1", "Release Type 2"],
                script="Script",
                track_total=10,
            ),
            track_info=TrackInfo(
                artist="Track Artist",
                artists=["Track Artist One", "Track Artist Two"],
                artists_sort=["One, Track Artist", "Two, Track Artist"],
                isrcs=["ISRCS 1", "ISRCS 2"],
                musicbrainz_artist_ids=["MB-Artist-ID-1", "MB-Artist-ID-2"],
                musicbrainz_release_track_id="MB-Release-Track-ID",
                musicbrainz_track_id="MB-Track_ID",
                title="Track Title",
                track_number=3,
            ),
        )
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = open_(test_file.name)
                f._info = info
                f.write_tags()
                old_info = copy.deepcopy(info)
                new_info = f.read_tags()
                if src.suffix == ".m4a":
                    old_info.relation_info.performers = None  # m4a doesn't save performers
                    old_info.release_info.front_cover.desc = None  # m4a doesn't save cover desc
                if src.suffix == ".mp3":
                    old_info.release_info.original_date = None  # mp3 doesn't save orig date
                self.assertEqual(old_info, new_info, f"Blank file modified for {src.suffix}")


def _audio_file_copy(src_filepath):
    # Create a copy of the given source file and return the copy as a context-manager.
    #
    # We work with a temp copy of the file so we don't break our test data
    dst = tempfile.NamedTemporaryFile(mode="wb", prefix="test_", suffix=src_filepath.suffix)
    dst.write(src_filepath.read_bytes())
    dst.flush()
    dst.seek(0)
    return contextlib.closing(dst)
