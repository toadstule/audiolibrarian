# Copyright (C) 2020 Stephen Jibson
#
# This file is part of AudioLibrarian.
#
# AudioLibrarian is free software: you can redistribute it and/or modify it under the terms of the
# GNU General Public License as published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.
#
# AudioLibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
# without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
# the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with Foobar.  If not, see
# <https://www.gnu.org/licenses/>.
#

from unittest import TestCase

from audiolibrarian import text


class TestText(TestCase):
    def test__alpha_numeric_key(self):
        for initial, expected in (
            ([], []),
            (["b", "a", "c"], ["a", "b", "c"]),
            (["3", "2", "1"], ["1", "2", "3"]),
            (["9", "10", "5"], ["5", "9", "10"]),
            (["6_six", "10_ten", "1_one", "11_eleven"], ["1_one", "6_six", "10_ten", "11_eleven"]),
        ):
            self.assertListEqual(expected, sorted(initial, key=text.alpha_numeric_key))

    def test__comma_and_join(self):
        self.assertEqual("", text.join([]))
        self.assertEqual("a", text.join(["a"]))
        self.assertEqual("aa", text.join(["aa"]))
        self.assertEqual("aa and bb", text.join(["aa", "bb"]))
        self.assertEqual("aa, bb and cc", text.join(["aa", "bb", "cc"]))
        self.assertEqual("aa, bb, cc and dd", text.join(["aa", "bb", "cc", "dd"]))
        self.assertEqual("", text.join([], joiner="; "))
        self.assertEqual("a", text.join(["a"], joiner="; "))
        self.assertEqual("aa", text.join(["aa"], joiner="; "))
        self.assertEqual("aa and bb", text.join(["aa", "bb"], joiner="; "))
        self.assertEqual("aa; bb and cc", text.join(["aa", "bb", "cc"], joiner="; "))
        self.assertEqual("aa; bb; cc and dd", text.join(["aa", "bb", "cc", "dd"], joiner="; "))
        self.assertEqual("", text.join([], word="or"))
        self.assertEqual("a", text.join(["a"], word="or"))
        self.assertEqual("aa", text.join(["aa"], word="or"))
        self.assertEqual("aa or bb", text.join(["aa", "bb"], word="or"))
        self.assertEqual("aa, bb or cc", text.join(["aa", "bb", "cc"], word="or"))
        self.assertEqual("aa, bb, cc or dd", text.join(["aa", "bb", "cc", "dd"], word="or"))

    def test__fix(self):
        self.assertEqual("", text.fix(""))
        self.assertEqual("abc", text.fix("abc"))
        self.assertEqual("a-b", text.fix("a-b"))
        self.assertEqual("a-b", text.fix(f"a{chr(8208)}b"))
        self.assertEqual("a-b", text.fix(f"a{chr(8211)}b"))
        self.assertEqual("'your_mom'", text.fix(f"{chr(8216)}your_mom{chr(8217)}"))
        self.assertEqual("one...two", text.fix("one…two"))
        self.assertEqual("one...two", text.fix(f"one{chr(8230)}two"))
        self.assertEqual("é", text.fix("é"), "fix should not drop accents")

    def test__get_filename(self):
        self.assertEqual("your_mom", text.get_filename("your_mom"))
        self.assertEqual("your_mom", text.get_filename("your mom"))
        self.assertEqual("your_mom", text.get_filename("your mom!"))
        self.assertEqual("your.mom", text.get_filename("your.mom"))
        self.assertEqual("your__mom", text.get_filename("your (mom)"))
        self.assertEqual("your__mom", text.get_filename("your [mom]"))
        self.assertEqual("your_mom_and_me", text.get_filename("your mom & me"))
        self.assertEqual("e", text.get_filename("é"), "get_filename should drop accents")

    def test__get_uuid(self):
        input_ = "your mom"
        expected = None
        self.assertEqual(expected, text.get_uuid(input_))

        input_ = "123e4567-e89b-12d3-a456-426614174000"
        expected = input_
        self.assertEqual(expected, text.get_uuid(input_))

        input_ = "https://musicbrainz.org/artist/3630fff3-52fc-4e97-ab01-d68fd88e4135"
        expected = "3630fff3-52fc-4e97-ab01-d68fd88e4135"
        self.assertEqual(expected, text.get_uuid(input_))

        input_ = "11111111-e89b-12d3-a456-426614174000 and 22222222-e89b-12d3-a456-426614174000"
        expected = "11111111-e89b-12d3-a456-426614174000"
        self.assertEqual(expected, text.get_uuid(input_))
