#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for library_layout."""

import pathlib

import pytest

from audiolibrarian.domain.model import record, release, values
from audiolibrarian.domain.model.track import Track
from audiolibrarian.domain.model.values import MediumPosition
from audiolibrarian.domain.services import library_layout


def test__artist_year_album_path() -> None:
    """Library-layout should generate correct artist/album path."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=record.ListF(["Artist, The"]),
        original_year="2020",
    )
    path = library_layout.artist_year_album_path(release_obj)
    assert path == pathlib.Path("Artist,_The/2020__The_Album")


def test__artist_year_album_path_missing_artists_raises_error() -> None:
    """Release without artists should raise ValueError."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=None,
        original_year="2020",
    )
    with pytest.raises(ValueError, match="Unable to determine artist path"):
        library_layout.artist_year_album_path(release_obj)


def test__artist_year_album_path_missing_year_raises_error() -> None:
    """Release without year should raise ValueError."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=record.ListF(["Artist, The"]),
        original_year=None,
    )
    with pytest.raises(ValueError, match="Unable to determine album path"):
        library_layout.artist_year_album_path(release_obj)


def test__artist_year_album_disc_path_single_disc() -> None:
    """Library-layout should generate correct artist/album/disc path."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=record.ListF(["Artist, The"]),
        original_year="2020",
    )
    medium_position = MediumPosition(number=1, count=1)
    path = library_layout.artist_year_album_disc_path(release=release_obj, medium_position=medium_position)
    assert path == pathlib.Path("Artist,_The/2020__The_Album")


def test__artist_year_album_disc_path_multiple_disc() -> None:
    """Library-layout should generate correct artist/album/disc path."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=record.ListF(["Artist, The"]),
        original_year="2020",
    )
    medium_position = MediumPosition(number=1, count=3)
    path = library_layout.artist_year_album_disc_path(release=release_obj, medium_position=medium_position)
    assert path == pathlib.Path("Artist,_The/2020__The_Album/disc1")


def test_full_path() -> None:
    """Full path should generate correct path."""
    release_obj = release.Release(
        album="The Album",
        album_artists_sort=record.ListF(["Artist, The"]),
        original_year="2020",
    )
    medium_position = MediumPosition(number=1, count=3)
    path = library_layout.full_path(
        root_path=pathlib.Path("/test_library"),
        format_tree_name=library_layout.FormatTreeName.FLAC,
        release=release_obj,
        medium_position=medium_position,
    )
    assert path == pathlib.Path("/test_library/flac/Artist,_The/2020__The_Album/disc1")


def test__track_get_filename() -> None:
    """Track should generate filename correctly."""
    track_obj = Track(
        title="Track Title",
        track_number=values.TrackNumber(3),
    )
    assert library_layout.track_filename(track_obj) == "03__Track_Title"


def test__track_get_filename_with_suffix() -> None:
    """Track should generate filename with suffix correctly."""
    track_obj = Track(
        title="Track Title",
        track_number=values.TrackNumber(5),
    )
    assert library_layout.track_filename(track_obj, suffix=".flac") == "05__Track_Title.flac"


def test__track_get_filename_missing_title_raises_error() -> None:
    """Track without title should raise ValueError when generating filename."""
    track_obj = Track(
        title=None,
        track_number=values.TrackNumber(1),
    )
    with pytest.raises(ValueError, match="Unable to generate a filename"):
        library_layout.track_filename(track_obj)


def test__track_get_filename_missing_track_number_raises_error() -> None:
    """Track without track number should raise ValueError when generating filename."""
    track_obj = Track(
        title="Track Title",
        track_number=None,
    )
    with pytest.raises(ValueError, match="Unable to generate a filename"):
        library_layout.track_filename(track_obj)
