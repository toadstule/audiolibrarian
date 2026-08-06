#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test the user_input module."""

from typing import Final
from unittest.mock import patch

from audiolibrarian.common import user_input


class TestUserInput:
    """Test the user_input module."""

    _VALID_UUID: Final[str] = "3f2504e0-4f89-4b23-a555-7b19816df8ea"

    def test_input_int(self) -> None:
        """Test the input_int function."""
        with patch("builtins.input", return_value="1"):
            assert user_input.input_int("Enter an integer: ") == 1

    def test_input_int_invalid(self) -> None:
        """Test that the input_int function retries on invalid input."""
        with patch("builtins.input", side_effect=["a", "2"]):
            assert user_input.input_int("Enter an integer: ") == 2

    def test_input_int_invalid_min_max(self) -> None:
        """Test that the input_int function retries on invalid input and min/max."""
        with patch("builtins.input", side_effect=["-1", "0", "9", "10", "21", "14"]):
            assert user_input.input_int("Enter an integer: ", min_=10, max_=20) == 10
            assert user_input.input_int("Enter an integer: ", min_=10, max_=20) == 14

    def test_input_str(self) -> None:
        """Test the input_str function."""
        with patch("builtins.input", return_value="test"):
            assert user_input.input_str("Enter a string: ") == "test"

    def test_input_uuid(self) -> None:
        """Test the input_uuid function."""
        with patch("builtins.input", return_value=self._VALID_UUID):
            assert user_input.input_uuid("Enter a UUID: ") == self._VALID_UUID

    def test_input_uuid_invalid(self) -> None:
        """Test that the input_uuid function retries on invalid input."""
        with patch("builtins.input", side_effect=["test", self._VALID_UUID]):
            assert user_input.input_uuid("Enter a UUID: ") == self._VALID_UUID
