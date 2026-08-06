#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test AudioFile."""

import contextlib
import copy
import hashlib
import pathlib
import tempfile
from collections.abc import Generator
from pathlib import Path
from typing import Any

import attrs
import pytest

from audiolibrarian.application.ports.tag_gateway import TagGatewayP
from audiolibrarian.audiofile import audiofile
from audiolibrarian.domain.model import enums, medium, record, release, track, values

test_data_path = (Path(__file__).parents[2] / "test_data").resolve()


def _normalize_onetrack_for_comparison(one_track: release.OneTrack, suffix: str) -> release.OneTrack:
    """Normalize a OneTrack for comparison by removing file-specific and format-specific metadata.

    Test helper function for comparing OneTrack objects from different sources.
    """
    if not one_track.release or not one_track.release.media or not one_track.medium_position:
        return one_track
    medium_num = one_track.medium_position.number
    if medium_num not in one_track.release.media:
        return one_track
    medium_obj = one_track.release.media[medium_num]
    if not medium_obj.tracks or not one_track.track_number:
        return one_track
    track_obj = medium_obj.tracks[one_track.track_number]
    track_without_info = attrs.evolve(track_obj, file_info=None)
    medium_without_info = attrs.evolve(
        medium_obj, tracks={**medium_obj.tracks, one_track.track_number: track_without_info}
    )
    release_without_info = attrs.evolve(
        one_track.release, media={**one_track.release.media, medium_num: medium_without_info}
    )
    result = attrs.evolve(one_track, release=release_without_info)

    # Handle format-specific differences
    if suffix == ".m4a" and result.release:
        # m4a doesn't save performers or cover desc.
        if result.release.people:
            release_without_info = attrs.evolve(
                result.release, people=attrs.evolve(result.release.people, performers=None)
            )
            result = attrs.evolve(result, release=release_without_info)
        if result.release.front_cover:
            release_without_info = attrs.evolve(
                result.release, front_cover=attrs.evolve(result.release.front_cover, desc=None)
            )
            result = attrs.evolve(result, release=release_without_info)
    elif suffix == ".mp3" and result.release:
        # mp3 doesn't save original_date.
        result = attrs.evolve(result, release=attrs.evolve(result.release, original_date=None))

    return result


class TestAudioFile:
    """Test AudioFile."""

    _blank_test_files = (p.resolve() for p in test_data_path.glob("00.*"))

    @pytest.fixture
    def test_data(self) -> Generator[None]:
        """Set up the tests."""
        self._verify_test_data()
        yield None
        self._verify_test_data()

    @staticmethod
    def _verify_test_data() -> None:
        """Verify that our test data files haven't been modified.

        See test_data/README.md for more info.
        """
        with (test_data_path / "checksums").open() as checksum_file:
            for line in checksum_file:
                checksum, filename = line.strip().split()
                filepath = test_data_path / filename
                got = hashlib.md5(filepath.read_bytes()).hexdigest()
                assert checksum == got, f"Mismatched checksum for {filepath}"

    def test__protocol_compliance(self) -> None:
        """Test protocol compliance."""
        src = next(self._blank_test_files)
        with _audio_file_copy(src) as test_file:
            audio_file_instance = audiofile.AudioFile.open(test_file.name)
        # noinspection protocol
        assert isinstance(audio_file_instance, TagGatewayP), "AudioFile does not implement TagGatewayP."

    def test__no_changes_rw(self, test_data: Generator[None]) -> None:
        """Verify that a read/write cycle doesn't change any tags."""
        _ = test_data
        extensions = (".flac", ".m4a", ".mp3")
        for src in [p.resolve() for p in test_data_path.glob("*") if p.suffix in extensions]:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                before = dict(f._mut_file.tags or {})
                f.write_tags()
                after = dict(f._mut_file.tags or {})

            # TIPL can be in any order, so we'll compare it separately and remove it.
            tipl_before, tipl_after = [], []
            if t := before.get("TIPL"):
                tipl_before = sorted(t.people)
                del before["TIPL"]
            if t := after.get("TIPL"):
                tipl_after = sorted(t.people)
                del after["TIPL"]
            assert tipl_after == tipl_before, f"TIPL changed in {src}"
            assert after == before, f"Tags changed in {src}"

    def test__no_changes_wr_blank(self, test_data: Generator[None]) -> None:
        """Verify that a write/read cycle doesn't change any blank tags."""
        _ = test_data
        blank_info = release.OneTrack()
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                f.one_track = blank_info
                f.write_tags()
                info = f.read_tags()
                assert info == blank_info, f"Blank file modified for {src.suffix}"
                assert f.__repr__().startswith("AudioFile: /")

    def test__no_changes_wr(self, test_data: Generator[None]) -> None:
        """Verify that a write/read cycle doesn't change any tags."""
        _ = test_data
        info = release.OneTrack(
            release=release.Release(
                album="Album",
                album_artists=record.ListF(["Album Artist One", "Album Artist Two"]),
                album_artists_sort=record.ListF(["One, Album Artist", "Two, Album Artist"]),
                asins=["ASIN 1", "ASIN 2"],
                barcodes=["Barcode 1", "Barcode 2"],
                catalog_numbers=["Catalog Number 1", "Catalog Number 2"],
                date="2015-09-24",
                front_cover=values.FrontCover(data=b"", desc="front", mime="image/jpg"),
                genres=record.ListF(["Genre 1", "Genre 2"]),
                labels=["Label 1", "Label 2"],
                media={
                    7: medium.Medium(
                        formats=record.ListF(["Media 1 Format"]),
                        titles=["Disc title 1", "Disc title 2"],
                        track_count=10,
                        tracks={
                            values.TrackNumber(3): track.Track(
                                artist="Track Artist",
                                artists=record.ListF(["Track Artist One", "Track Artist Two"]),
                                artists_sort=["One, Track Artist", "Two, Track Artist"],
                                isrcs=["ISRCS 1", "ISRCS 2"],
                                musicbrainz_artist_ids=record.ListF(["MB-Artist-ID-1", "MB-Artist-ID-2"]),
                                musicbrainz_release_track_id="MB-Release-Track-ID",
                                musicbrainz_track_id="MB-Track_ID",
                                title="Track Title",
                                track_number=values.TrackNumber(3),
                            )
                        },
                    )
                },
                medium_count=14,
                musicbrainz_album_artist_ids=record.ListF(["MB-Album-Artist-ID-1", "MB-Album-Artist-ID-2"]),
                musicbrainz_album_id="MB-Album-ID",
                musicbrainz_release_group_id="MB-Release-Group_ID",
                original_date="1972-04-02",
                original_year="1992",
                people=values.People(
                    engineers=["Engineer 1", "Engineer 2"],
                    lyricists=["Lyricist 1", "Lyricist 2"],
                    mixers=["Mixer 1", "Mixer 2"],
                    performers=[
                        values.Performer(name="Performer 1", instrument="Instrument 1"),
                        values.Performer(name="Performer 2", instrument="Instrument 2"),
                    ],
                    producers=["Producer 1", "Producer 2"],
                ),
                release_countries=["Release Country 1", "Release Country 2"],
                release_statuses=["Release Status 1", "Release Status 2"],
                release_types=["Release Type 1", "Release Type 2"],
                script="Script",
                source=enums.Source.TAGS,
            ),
            medium_position=values.MediumPosition(number=7, count=14),
            track_number=values.TrackNumber(3),
        )
        for src in self._blank_test_files:
            with _audio_file_copy(src) as test_file:
                f = audiofile.AudioFile.open(test_file.name)
                f._one_track = info
                f.write_tags()
                old_info = copy.deepcopy(info)
                new_info = f.read_tags()

                # Remove stuff we don't want to check.
                new_info = _normalize_onetrack_for_comparison(new_info, src.suffix)
                old_info = _normalize_onetrack_for_comparison(old_info, src.suffix)
                assert new_info == old_info, f"Write/Read failed for {src.suffix}"


class TestAudioFileMisc:
    """Test AudioFile miscellaneous functions."""

    def test__file_not_found(self) -> None:
        """Test file-not-found."""
        with pytest.raises(FileNotFoundError):
            audiofile.AudioFile.open("your_mom_goes_to_college.mp3")

    def test__file_not_supported(self) -> None:
        """Test file-not-supported."""
        with pytest.raises(NotImplementedError):
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
