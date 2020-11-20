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

import audiolibrarian


class TestMisc(TestCase):
    def setUp(self) -> None:
        self._required_exe = audiolibrarian.REQUIRED_EXE[:]

    def tearDown(self) -> None:
        audiolibrarian.REQUIRED_EXE = self._required_exe[:]

    def test__check_deps_true(self) -> None:
        audiolibrarian.REQUIRED_EXE = ["ls", "ps"]
        self.assertTrue(audiolibrarian.check_deps())

    def test__check_deps_false(self) -> None:
        audiolibrarian.REQUIRED_EXE = ["your_mom_goes_to_college"]
        self.assertFalse(audiolibrarian.check_deps())
