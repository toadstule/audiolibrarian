#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for Track."""

import pytest

from audiolibrarian.domain.model import track, values


class TestTrack:
    """Tests for Track entity."""

    def test__track_creation(self) -> None:
        """Track with valid fields should be created successfully."""
        track_obj = track.Track(
            artist="Artist Name",
            title="Track Title",
            track_number=values.TrackNumber(1),
        )
        assert track_obj.artist == "Artist Name"
        assert track_obj.title == "Track Title"
        assert track_obj.track_number == values.TrackNumber(1)

    def test__track_get_filename(self) -> None:
        """Track should generate filename correctly."""
        track_obj = track.Track(
            title="Track Title",
            track_number=values.TrackNumber(3),
        )
        assert track_obj.get_filename() == "03__Track_Title"

    def test__track_get_filename_with_suffix(self) -> None:
        """Track should generate filename with suffix correctly."""
        track_obj = track.Track(
            title="Track Title",
            track_number=values.TrackNumber(5),
        )
        assert track_obj.get_filename(suffix=".flac") == "05__Track_Title.flac"

    def test__track_get_filename_missing_title_raises_error(self) -> None:
        """Track without title should raise ValueError when generating filename."""
        track_obj = track.Track(
            title=None,
            track_number=values.TrackNumber(1),
        )
        with pytest.raises(ValueError, match="Unable to generate a filename"):
            track_obj.get_filename()

    def test__track_get_filename_missing_track_number_raises_error(self) -> None:
        """Track without track number should raise ValueError when generating filename."""
        track_obj = track.Track(
            title="Track Title",
            track_number=None,
        )
        with pytest.raises(ValueError, match="Unable to generate a filename"):
            track_obj.get_filename()
