#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test output."""

import time

import pytest

from audiolibrarian.output import Dots


class TestDots:
    """Test dot generation."""

    def test__dots(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Test dots."""
        with Dots("Please wait") as d:
            for _ in range(5):
                time.sleep(0.01)
                d.dot()
        output = capsys.readouterr().out.strip()
        assert output == "Please wait....."
