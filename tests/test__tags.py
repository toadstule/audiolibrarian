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

from audiolibrarian.audiofile.tags import Tags


class TestTags(TestCase):
    def test__tags(self) -> None:
        t = Tags()
        t["a"] = "A"
        t["b"] = "B"
        t["c"] = None
        expected = {"a": "A", "b": "B"}
        self.assertDictEqual(expected, t)

    def test__tags_init(self) -> None:
        t = Tags({"a": "A", "b": "B", "c": None})
        expected = {"a": "A", "b": "B"}
        self.assertDictEqual(expected, t)

    def test__tags_list(self) -> None:
        t = Tags()
        t["a"] = "A"
        t["b"] = [None]
        t["c"] = ["c", None]
        t["d"] = ["None"]
        t["e"] = {"1": None}
        expected = {"a": "A"}
        self.assertDictEqual(expected, t)
