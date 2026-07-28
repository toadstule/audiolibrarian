#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for domain value objects."""

import attrs
import pytest

from audiolibrarian.domain.model.values import AudioFormat, MediumPosition, TrackNumber


class TestDiscPosition:
    """Tests for MediumPosition value object."""

    def test__valid_disc_position(self) -> None:
        """Disc position with valid number should be created successfully."""
        position = MediumPosition(number=1, count=2)
        assert position.number == 1
        assert position.count == 2

    def test__disc_position_at_lower_bound(self) -> None:
        """Disc position with number = 1 should be valid."""
        position = MediumPosition(number=1, count=3)
        assert position.number == 1

    def test__disc_position_at_upper_bound(self) -> None:
        """Disc position with number = count should be valid."""
        position = MediumPosition(number=3, count=3)
        assert position.number == 3

    def test__disc_position_middle_value(self) -> None:
        """Disc position with number in the middle should be valid."""
        position = MediumPosition(number=2, count=3)
        assert position.number == 2

    def test__disc_position_number_too_low_raises_error(self) -> None:
        """Disc position with number < 1 should raise ValueError."""
        with pytest.raises(ValueError, match=r"number must be between 1 and count \(2\)"):
            MediumPosition(number=0, count=2)

    def test__disc_position_number_negative_raises_error(self) -> None:
        """Disc position with negative number should raise ValueError."""
        with pytest.raises(ValueError, match=r"number must be between 1 and count \(2\)"):
            MediumPosition(number=-1, count=2)

    def test__disc_position_number_too_high_raises_error(self) -> None:
        """Disc position with number > count should raise ValueError."""
        with pytest.raises(ValueError, match=r"number must be between 1 and count \(2\)"):
            MediumPosition(number=3, count=2)

    def test__disc_position_single_disc(self) -> None:
        """Single disc should have number = 1 and count = 1."""
        position = MediumPosition(number=1, count=1)
        assert position.number == 1
        assert position.count == 1

    def test__disc_position_is_frozen(self) -> None:
        """MediumPosition should be immutable (frozen)."""
        position = MediumPosition(number=1, count=2)
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            # noinspection dataclass
            position.number = 2  # type: ignore[misc]

    def test__disc_position_bool_true(self) -> None:
        """MediumPosition with values should evaluate to True."""
        position = MediumPosition(number=1, count=2)
        assert position

    def test__disc_position_asdict(self) -> None:
        """MediumPosition should convert to dict correctly."""
        position = MediumPosition(number=2, count=3)
        result = position.asdict()
        assert result == {"number": 2, "count": 3}


class TestTrackNumber:
    """Tests for TrackNumber value object."""

    def test__valid_track_number(self) -> None:
        """Track number with valid value should be created successfully."""
        track = TrackNumber(5)
        assert track.value == 5

    def test__track_number_single_digit(self) -> None:
        """Track number with single digit should be created successfully."""
        track = TrackNumber(value=3)
        assert track.value == 3

    def test__track_number_double_digit(self) -> None:
        """Track number with double digit should be created successfully."""
        track = TrackNumber(value=12)
        assert track.value == 12

    def test__track_number_negative_raises_error(self) -> None:
        """Track number with negative value should raise ValueError."""
        with pytest.raises(ValueError, match=r"'value' must be >= 0"):
            TrackNumber(value=-1)

    def test__track_number_from_filename(self) -> None:
        """Track number should be extracted from filename correctly."""
        track = TrackNumber.from_filename("07__always_look_on_the_bright_side.mp3")
        assert track.value == 7

    def test__track_number_from_filename_single_digit(self) -> None:
        """Track number from filename with single digit should work."""
        track = TrackNumber.from_filename("01__spam_song.mp3")
        assert track.value == 1

    def test__track_number_from_filename_double_digit(self) -> None:
        """Track number from filename with double digit should work."""
        track = TrackNumber.from_filename("15__the_lumberjack_song.mp3")
        assert track.value == 15

    def test__track_number_str_single_digit(self) -> None:
        """Track number string representation should pad single digit with zero."""
        track = TrackNumber(value=3)
        assert str(track) == "03"

    def test__track_number_str_double_digit(self) -> None:
        """Track number string representation should not pad double digit."""
        track = TrackNumber(value=12)
        assert str(track) == "12"

    def test__track_number_str_zero(self) -> None:
        """Track number string representation should pad zero."""
        track = TrackNumber(value=0)
        assert str(track) == "00"

    def test__track_number_is_frozen(self) -> None:
        """TrackNumber should be immutable (frozen)."""
        track = TrackNumber(value=5)
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            # noinspection dataclass
            track.value = 10  # type: ignore[misc]

    def test__track_number_bool_true(self) -> None:
        """TrackNumber with value should evaluate to True."""
        track = TrackNumber(value=7)
        assert track

    def test__track_number_asdict(self) -> None:
        """TrackNumber should convert to dict correctly."""
        track = TrackNumber(value=8)
        result = track.asdict()
        assert result == {"value": 8}


class TestAudioFormat:
    """Tests for AudioFormat value object."""

    def test__audio_format_flac(self) -> None:
        """AudioFormat for FLAC should be created successfully."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.FLAC)
        assert format_obj.file_type == enums.FileType.FLAC

    def test__audio_format_m4a(self) -> None:
        """AudioFormat for M4A (AAC) should be created successfully."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.AAC)
        assert format_obj.file_type == enums.FileType.AAC

    def test__audio_format_mp3(self) -> None:
        """AudioFormat for MP3 should be created successfully."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.MP3)
        assert format_obj.file_type == enums.FileType.MP3

    def test__audio_format_is_frozen(self) -> None:
        """AudioFormat should be immutable (frozen)."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.FLAC)
        with pytest.raises(attrs.exceptions.FrozenInstanceError):
            # noinspection dataclass
            format_obj.file_type = enums.FileType.MP3  # type: ignore[misc]

    def test__audio_format_bool_true(self) -> None:
        """AudioFormat with value should evaluate to True."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.FLAC)
        assert format_obj

    def test__audio_format_asdict(self) -> None:
        """AudioFormat should convert to dict correctly."""
        from audiolibrarian.domain.model import enums

        format_obj = AudioFormat(file_type=enums.FileType.MP3)
        result = format_obj.asdict()
        assert result == {"file_type": enums.FileType.MP3}
