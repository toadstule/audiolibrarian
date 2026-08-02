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
