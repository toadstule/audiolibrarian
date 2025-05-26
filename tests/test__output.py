"""Test output."""

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
