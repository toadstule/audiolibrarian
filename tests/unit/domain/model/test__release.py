#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for Release and OneTrack."""

import pathlib

import pytest

from audiolibrarian.domain.model import medium, record, release, track, values


class TestRelease:
    """Tests for Release entity."""

    def test__release_creation(self) -> None:
        """Release with valid fields should be created successfully."""
        release_obj = release.Release(
            album="Test Album",
            album_artists=record.ListF(["Artist One", "Artist Two"]),
            album_artists_sort=record.ListF(["One, Artist", "Two, Artist"]),
            date="2020-01-01",
            original_year="2020",
        )
        assert release_obj.album == "Test Album"
        assert release_obj.album_artists == record.ListF(["Artist One", "Artist Two"])
        assert release_obj.date == "2020-01-01"
        assert release_obj.original_year == "2020"

    def test__release_pp(self) -> None:
        """Release should generate correct pretty print string."""
        track1 = track.Track(title="Track 1", track_number=values.TrackNumber(1))
        track2 = track.Track(title="Track 2", track_number=values.TrackNumber(2))
        medium_obj = medium.Medium(
            track_count=2,
            tracks={
                values.TrackNumber(1): track1,
                values.TrackNumber(2): track2,
            },
        )
        release_obj = release.Release(
            album="Test Album",
            album_artists=record.ListF(["Artist"]),
            medium_count=1,
            media={1: medium_obj},
        )
        result = release_obj.pp(1)
        assert "Album: Test Album" in result
        assert "Artist(s): Artist" in result
        assert "Medium: 1 of 1" in result
        assert "  01: Track 1" in result
        assert "  02: Track 2" in result

    def test__release_pp_missing_media_raises_error(self) -> None:
        """Release without media should raise ValueError."""
        release_obj = release.Release(album="Test Album")
        with pytest.raises(ValueError, match="Missing release information"):
            release_obj.pp(1)

    def test__release_pp_missing_medium_shows_no_tracks(self) -> None:
        """Release with media but missing specific medium should show no tracks."""
        medium_obj = medium.Medium(
            track_count=2,
            tracks={values.TrackNumber(1): track.Track(title="Track 1", track_number=values.TrackNumber(1))},
        )
        release_obj = release.Release(
            album="Test Album",
            album_artists=record.ListF(["Artist"]),
            medium_count=2,
            media={1: medium_obj},
        )
        result = release_obj.pp(2)
        assert "Album: Test Album" in result
        assert "Artist(s): Artist" in result
        assert "Medium: 2 of 2" in result
        assert "  (no tracks)" in result

    def test__release_pp_medium_without_tracks_shows_no_tracks(self) -> None:
        """Release with medium but no tracks should show no tracks."""
        medium_obj = medium.Medium(track_count=0, tracks=None)
        release_obj = release.Release(
            album="Test Album",
            album_artists=record.ListF(["Artist"]),
            medium_count=1,
            media={1: medium_obj},
        )
        result = release_obj.pp(1)
        assert "Album: Test Album" in result
        assert "Artist(s): Artist" in result
        assert "Medium: 1 of 1" in result
        assert "  (no tracks)" in result


class TestOneTrack:
    """Tests for OneTrack entity."""

    def test__onetrack_creation(self) -> None:
        """OneTrack with valid fields should be created successfully."""
        release_obj = release.Release(album="Test Album")
        medium_position = values.MediumPosition(number=1, count=1)
        track_number = values.TrackNumber(1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=track_number,
        )
        assert onetrack.release == release_obj
        assert onetrack.medium_position == medium_position
        assert onetrack.track_number == track_number

    def test__onetrack_medium_property(self) -> None:
        """OneTrack should return correct Medium."""
        track1 = track.Track(title="Track 1", track_number=values.TrackNumber(1))
        medium_obj = medium.Medium(
            track_count=1,
            tracks={values.TrackNumber(1): track1},
        )
        release_obj = release.Release(
            album="Test Album",
            media={1: medium_obj},
        )
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        assert onetrack.medium == medium_obj

    def test__onetrack_medium_property_none_without_release(self) -> None:
        """OneTrack without release should return None for medium."""
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=None,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        assert onetrack.medium is None

    def test__onetrack_medium_property_none_without_media(self) -> None:
        """OneTrack without media should return None for medium."""
        release_obj = release.Release(album="Test Album", media=None)
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        assert onetrack.medium is None

    def test__onetrack_track_property(self) -> None:
        """OneTrack should return correct Track."""
        track1 = track.Track(title="Track 1", track_number=values.TrackNumber(1))
        medium_obj = medium.Medium(
            track_count=1,
            tracks={values.TrackNumber(1): track1},
        )
        release_obj = release.Release(
            album="Test Album",
            media={1: medium_obj},
        )
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        assert onetrack.track == track1

    def test__onetrack_track_property_none_without_medium(self) -> None:
        """OneTrack without medium should return None for track."""
        release_obj = release.Release(album="Test Album", media=None)
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        assert onetrack.track is None
