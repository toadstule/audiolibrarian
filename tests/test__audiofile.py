import hashlib
import tempfile
from pathlib import Path
from unittest import TestCase

from audiolibrarian.audiofile import open_


test_data_path = Path("test_data").resolve()


class TestFlac(TestCase):
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

    def test__no_changes(self) -> None:
        """Verify that a ready/write cycle doesn't change any tags."""
        for src in test_data_path.glob("*.flac"):
            # work with a temp copy of the file so we don't break our test data
            with tempfile.NamedTemporaryFile(mode="wb", prefix="test_", suffix=".flac") as dst:
                dst.write(src.read_bytes())
                f = open_(dst.name)
                before = dict(f._mut_file.tags)
                f.write_tags()
                after = dict(f._mut_file.tags)

            # self.assertSetEqual(set(before.keys()), set(after.keys()), f"Keys changed in {src}")
            self.assertDictEqual(before, after, f"Tags changed in {src}")
