#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for Release and OneTrack."""

import pathlib

import pytest

from audiolibrarian.domain.model import enums, medium, record, release, track, values


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

    def test__release_get_artist_album_path(self) -> None:
        """Release should generate correct artist/album path."""
        release_obj = release.Release(
            album="The Album",
            album_artists_sort=record.ListF(["Artist, The"]),
            original_year="2020",
        )
        path = release_obj.get_artist_album_path()
        assert path == pathlib.Path("Artist,_The/2020__The_Album")

    def test__release_get_artist_album_path_missing_artists_raises_error(self) -> None:
        """Release without artists should raise ValueError."""
        release_obj = release.Release(
            album="The Album",
            album_artists_sort=None,
            original_year="2020",
        )
        with pytest.raises(ValueError, match="Unable to determine artist path"):
            release_obj.get_artist_album_path()

    def test__release_get_artist_album_path_missing_year_raises_error(self) -> None:
        """Release without year should raise ValueError."""
        release_obj = release.Release(
            album="The Album",
            album_artists_sort=record.ListF(["Artist, The"]),
            original_year=None,
        )
        with pytest.raises(ValueError, match="Unable to determine album path"):
            release_obj.get_artist_album_path()

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

    def test__onetrack_get_artist_album_disc_path_single_medium(self) -> None:
        """OneTrack with single medium should return artist/album path."""
        release_obj = release.Release(
            album="The Album",
            album_artists_sort=record.ListF(["Artist, The"]),
            original_year="2020",
        )
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        path = onetrack.get_artist_album_disc_path()
        assert path == pathlib.Path("Artist,_The/2020__The_Album")

    def test__onetrack_get_artist_album_disc_path_multiple_mediums(self) -> None:
        """OneTrack with multiple mediums should return artist/album/disc path."""
        release_obj = release.Release(
            album="The Album",
            album_artists_sort=record.ListF(["Artist, The"]),
            original_year="2020",
        )
        medium_position = values.MediumPosition(number=2, count=3)
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        path = onetrack.get_artist_album_disc_path()
        assert path == pathlib.Path("Artist,_The/2020__The_Album/disc2")

    def test__onetrack_get_artist_album_disc_path_missing_medium_position_raises_error(self) -> None:
        """OneTrack without medium position should raise ValueError."""
        release_obj = release.Release(album="Test Album")
        onetrack = release.OneTrack(
            release=release_obj,
            medium_position=None,
            track_number=values.TrackNumber(1),
        )
        with pytest.raises(ValueError, match="Unable to determine path"):
            onetrack.get_artist_album_disc_path()

    def test__onetrack_get_artist_album_disc_path_missing_release_raises_error(self) -> None:
        """OneTrack without release should raise ValueError."""
        medium_position = values.MediumPosition(number=1, count=1)
        onetrack = release.OneTrack(
            release=None,
            medium_position=medium_position,
            track_number=values.TrackNumber(1),
        )
        with pytest.raises(ValueError, match="Unable to determine path"):
            onetrack.get_artist_album_disc_path()
