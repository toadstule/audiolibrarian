#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for Medium."""

import pytest

from audiolibrarian.domain.model import medium, record, track, values


class TestMedium:
    """Tests for Medium entity."""

    def test__medium_creation(self) -> None:
        """Medium with valid fields should be created successfully."""
        medium_obj = medium.Medium(
            formats=record.ListF(["CD"]),
            track_count=10,
        )
        assert medium_obj.formats == ["CD"]
        assert medium_obj.track_count == 10

    def test__medium_with_tracks(self) -> None:
        """Medium should be able to contain tracks."""
        track1 = track.Track(
            title="Track 1",
            track_number=values.TrackNumber(1),
        )
        track2 = track.Track(
            title="Track 2",
            track_number=values.TrackNumber(2),
        )
        medium_obj = medium.Medium(
            track_count=2,
            tracks={
                values.TrackNumber(1): track1,
                values.TrackNumber(2): track2,
            },
        )
        assert medium_obj.track_count == 2
        assert len(medium_obj.tracks) == 2
        assert medium_obj.tracks[values.TrackNumber(1)].title == "Track 1"
        assert medium_obj.tracks[values.TrackNumber(2)].title == "Track 2"

    def test__medium_with_titles(self) -> None:
        """Medium should be able to have disc titles."""
        medium_obj = medium.Medium(
            titles=["Disc 1", "Disc 2"],
        )
        assert medium_obj.titles == ["Disc 1", "Disc 2"]

    def test__medium_empty(self) -> None:
        """Medium can be created with no fields."""
        medium_obj = medium.Medium()
        assert medium_obj.formats is None
        assert medium_obj.titles is None
        assert medium_obj.track_count is None
        assert medium_obj.tracks is None
