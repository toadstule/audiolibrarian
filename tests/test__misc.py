#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#
from unittest import TestCase

from audiolibrarian import cli


class TestMisc(TestCase):
    def test__check_deps_true(self) -> None:
        cli_ = cli.CommandLineInterface(parse_args=False)
        cli_.required_exe = ["ls", "ps"]
        self.assertTrue(cli_._check_deps())

    def test__check_deps_false(self) -> None:
        cli_ = cli.CommandLineInterface(parse_args=False)
        cli_.required_exe = ["your_mom_goes_to_college"]
        self.assertFalse(cli_._check_deps())
