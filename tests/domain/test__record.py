#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tests for Record base class and ListF."""

import attrs

from audiolibrarian.domain.model.record import ListF, Record


@attrs.define
class KnightRecord(Record):
    """Test record for a brave knight."""

    name: str | None = None
    quests_completed: int | None = None
    has_shrubbery: bool | None = None


class TestListF:
    """Tests for ListF class."""

    def test__first__empty_list_returns_none(self) -> None:
        """Empty list should return None for first."""
        knights = ListF[str]()
        assert knights.first is None

    def test__first__single_element_returns_that_element(self) -> None:
        """List with one element should return that element."""
        knights = ListF[str](["King Arthur"])
        assert knights.first == "King Arthur"

    def test__first__multiple_elements_returns_first(self) -> None:
        """List with multiple elements should return the first one."""
        knights = ListF[str](["Sir Lancelot", "Sir Galahad", "Sir Robin"])
        assert knights.first == "Sir Lancelot"

    def test__first__with_none_values(self) -> None:
        """List with None values should still return the first element."""
        knights = ListF[str | None](["Sir Bedevere", None, "Sir Not-Appearing"])
        assert knights.first == "Sir Bedevere"

    def test__first__behaves_like_list(self) -> None:
        """ListF should still behave like a list for other operations."""
        knights = ListF[str](["Sir Lancelot", "Sir Galahad"])
        assert len(knights) == 2
        assert "Sir Galahad" in knights
        assert knights[1] == "Sir Galahad"


class TestRecordBool:
    """Tests for Record ``__bool__`` method."""

    def test__bool__knight_with_no_data_returns_false(self) -> None:
        """Knight with all None fields should evaluate to False (not a real knight)."""
        knight = KnightRecord()
        assert not knight

    def test__bool__knight_with_name_returns_true(self) -> None:
        """Knight with a name should evaluate to True."""
        knight = KnightRecord(name="Sir Lancelot")
        assert knight

    def test__bool__knight_with_quests_returns_true(self) -> None:
        """Knight with quests completed should evaluate to True."""
        knight = KnightRecord(quests_completed=3)
        assert knight

    def test__bool__knight_with_shrubbery_returns_true(self) -> None:
        """Knight with shrubbery should evaluate to True."""
        knight = KnightRecord(has_shrubbery=True)
        assert knight

    def test__bool__brave_sir_robin_returns_true(self) -> None:
        """Knight with all fields set should evaluate to True."""
        knight = KnightRecord(name="Sir Robin", quests_completed=1, has_shrubbery=True)
        assert knight

    def test__bool__knight_with_zero_values_returns_true(self) -> None:
        """Knight with zero values (0, False, '') should evaluate to True."""
        knight = KnightRecord(name="", quests_completed=0, has_shrubbery=False)
        assert knight


class TestRecordAsdict:
    """Tests for Record ``asdict`` method."""

    def test__asdict__empty_knight(self) -> None:
        """Empty knight should return dict with all None values."""
        knight = KnightRecord()
        result = knight.asdict()
        assert result == {"name": None, "quests_completed": None, "has_shrubbery": None}

    def test__asdict__knight_with_name(self) -> None:
        """Knight with name should return dict with that value."""
        knight = KnightRecord(name="Sir Galahad")
        result = knight.asdict()
        assert result == {"name": "Sir Galahad", "quests_completed": None, "has_shrubbery": None}

    def test__asdict__knight_with_quests(self) -> None:
        """Knight with quests should return dict with that value."""
        knight = KnightRecord(quests_completed=42)
        result = knight.asdict()
        assert result == {"name": None, "quests_completed": 42, "has_shrubbery": None}

    def test__asdict__knight_of_ni(self) -> None:
        """Knight of Ni with all fields set should return dict with all values."""
        knight = KnightRecord(name="Knight of Ni", quests_completed=1, has_shrubbery=True)
        result = knight.asdict()
        assert result == {"name": "Knight of Ni", "quests_completed": 1, "has_shrubbery": True}

    def test__asdict__returns_new_dict(self) -> None:
        """A record's asdict should return a new dict, not a reference."""
        knight = KnightRecord(name="King Arthur")
        result1 = knight.asdict()
        result2 = knight.asdict()
        assert result1 is not result2
        assert result1 == result2
