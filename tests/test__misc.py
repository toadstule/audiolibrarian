"""Miscellaneous tests."""

import pytest

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
from audiolibrarian import cli


class TestMisc:
    """Test miscellaneous functions."""

    @pytest.fixture(scope="class")
    def cli_(self) -> cli.CommandLineInterface:
        """Return a cli instance."""
        return cli.CommandLineInterface(parse_args=False)

    def test__check_deps_true(self, cli_: cli.CommandLineInterface) -> None:
        """Test dependency checker."""
        cli_.required_exe = {"ls", "ps"}  # type: ignore[misc]
        assert cli_._check_deps()

    def test__check_deps_false(self, cli_: cli.CommandLineInterface) -> None:
        """Test dependency checker."""
        cli_.required_exe = {"your_mom_goes_to_college"}  # type: ignore[misc]
        assert not cli_._check_deps()
