"""Test tags."""
#
#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#

import pytest

from audiolibrarian.audiofile.tags import Tags


class TestTags:
    """Test tags."""

    @pytest.fixture
    def tags(self) -> Tags:
        """Return a Tags instance."""
        return Tags()

    def test__tags(self, tags: Tags) -> None:
        """Test tags."""
        tags["a"] = "A"
        tags["b"] = "B"
        tags["c"] = None  # Should be dropped.
        expected = {"a": "A", "b": "B"}
        assert tags == expected

    @pytest.mark.parametrize(
        ("initial", "key", "value", "expected"),
        [
            ({}, "new_key", "value", {"new_key": "value"}),  # New key.
            ({"key": "old"}, "key", "new", {"key": "new"}),  # Update existing key.
            ({"key": "value"}, "key", None, {"key": "value"}),  # Update with None does nothing.
        ],
    )
    def test__tags_modification(
        self, initial: dict[str, str], key: str, value: str, expected: dict[str, str]
    ) -> None:
        """Test tag modification."""
        tags = Tags(initial)
        tags[key] = value
        assert tags == expected

    def test__tags_list(self, tags: Tags) -> None:
        """Test tags list."""
        tags["a"] = "A"
        tags["b"] = [None]
        tags["c"] = ["c", None]
        tags["d"] = ["None"]
        tags["e"] = {"1": None}
        expected = {"a": "A"}
        assert tags == expected
