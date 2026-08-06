#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test MusicBrainz."""

import logging
import os
from pathlib import Path

import attrs
import pytest

from audiolibrarian import config
from audiolibrarian.audiofile import audiofile
from audiolibrarian.domain.model import enums, release, values
from audiolibrarian.musicbrainz import MusicBrainzRelease
from tests.integration.infrastructure.test__audiofile import _audio_file_copy


def _normalize_release_for_comparison(release_obj: release.Release) -> release.Release:
    """Normalize a Release for comparison by removing fields we don't want to check.

    Test helper function for comparing Release objects from different sources.
    """
    evolved = release_obj
    # Remove genres, front_cover, asins, source
    evolved = attrs.evolve(evolved, genres=None, front_cover=None, asins=None, source=None)
    # Normalize people if present
    if evolved.people is not None:
        evolved = attrs.evolve(
            evolved, people=attrs.evolve(evolved.people, engineers=None, lyricists=None, mixers=None, producers=None)
        )
    return evolved


def _remove_file_info_from_release(
    release_obj: release.Release, medium_number: int, track_number: values.TrackNumber
) -> release.Release:
    """Remove file_info from a specific track in a Release.

    Test helper function for comparing Release objects without file-specific metadata.
    """
    if not release_obj.media or medium_number not in release_obj.media:
        return release_obj
    medium_obj = release_obj.media[medium_number]
    if not medium_obj.tracks or track_number not in medium_obj.tracks:
        return release_obj
    track_obj = medium_obj.tracks[track_number]
    track_without_info = attrs.evolve(track_obj, file_info=None)
    medium_without_info = attrs.evolve(medium_obj, tracks={**medium_obj.tracks, track_number: track_without_info})
    return attrs.evolve(release_obj, media={**release_obj.media, medium_number: medium_without_info})


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
                medium_number = f._one_track.medium_position.number
                track_number = f._one_track.track_number

            got = MusicBrainzRelease(
                release_id=expected.musicbrainz_album_id,
                settings=settings.musicbrainz,
            ).get_release()

            # Remove stuff we don't want to compare.
            expected = _normalize_release_for_comparison(expected)
            got = _normalize_release_for_comparison(got)

            # Remove file_info from the specific track
            expected = _remove_file_info_from_release(expected, medium_number, track_number)
            got = _remove_file_info_from_release(got, medium_number, track_number)

            if src.suffix == ".m4a" and got.people:  # We don't store this for m4a files.
                got = attrs.evolve(got, people=attrs.evolve(got.people, performers=None))

            if src.suffix == ".mp3":  # We don't store this for mp3 files.
                expected = attrs.evolve(expected, original_date=None)
                got = attrs.evolve(got, original_date=None)

            assert got.people == expected.people, f"People failed for {src}"
            expected = attrs.evolve(expected, people=None)
            got = attrs.evolve(got, people=None)

            # noinspection PyUnresolvedReferences
            assert (
                got.media[medium_number].tracks[track_number] == expected.media[medium_number].tracks[track_number]
            ), f"Track failed for {src}"
            # noinspection PyUnresolvedReferences
            expected = attrs.evolve(
                expected,
                media={
                    k: attrs.evolve(m, tracks=None) if k == medium_number else m
                    for k, m in (expected.media or {}).items()
                },
            )
            got = attrs.evolve(
                got,
                media={
                    k: attrs.evolve(m, tracks=None) if k == medium_number else m for k, m in (got.media or {}).items()
                },
            )

            # noinspection PyUnresolvedReferences
            assert got.media[medium_number] == expected.media[medium_number], f"Medium failed for {src}"
            expected = attrs.evolve(expected, media=None)
            got = attrs.evolve(got, media=None)

            assert expected.source == enums.Source.TAGS, f"Bad source from file read {src}"
            assert got.source == enums.Source.MUSICBRAINZ, f"Bad source from musicbrainz {src}"

            assert got == expected, f"Failed for {src}"
