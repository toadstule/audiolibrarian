"""Test text."""

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

from audiolibrarian import text


class TestText:
    """Test text functions."""

    @pytest.mark.parametrize(
        ("initial", "expected"),
        [
            ([], []),
            (["b", "a", "c"], ["a", "b", "c"]),
            (["3", "2", "1"], ["1", "2", "3"]),
            (["9", "10", "5"], ["5", "9", "10"]),
            (["6_six", "10_ten", "1_one", "11_eleven"], ["1_one", "6_six", "10_ten", "11_eleven"]),
        ],
    )
    def test__alpha_numeric_key(self, initial: list[str], expected: list[str]) -> None:
        """Test alphanumeric key sorting."""
        result = sorted(initial, key=text.alpha_numeric_key)
        assert result == expected

    @pytest.mark.parametrize(
        ("strings", "joiner", "word", "expected"),
        [
            ([], None, None, ""),
            (["a"], None, None, "a"),
            (["aa"], None, None, "aa"),
            (["aa", "bb"], None, None, "aa and bb"),
            (["aa", "bb", "cc"], None, None, "aa, bb and cc"),
            (["aa", "bb", "cc", "dd"], None, None, "aa, bb, cc and dd"),
            ([], "; ", None, ""),
            (["a"], "; ", None, "a"),
            (["aa"], "; ", None, "aa"),
            (["aa", "bb"], "; ", None, "aa and bb"),
            (["aa", "bb", "cc"], "; ", None, "aa; bb and cc"),
            (["aa", "bb", "cc", "dd"], "; ", None, "aa; bb; cc and dd"),
            ([], None, "or", ""),
            (["a"], None, "or", "a"),
            (["aa"], None, "or", "aa"),
            (["aa", "bb"], None, "or", "aa or bb"),
            (["aa", "bb", "cc"], None, "or", "aa, bb or cc"),
            (["aa", "bb", "cc", "dd"], None, "or", "aa, bb, cc or dd"),
            (["aa", "bb", "cc", "dd"], "; ", "or", "aa; bb; cc or dd"),
        ],
    )
    def test__comma_and_join(
        self, strings: list[str], joiner: str | None, word: str | None, expected: str
    ) -> None:
        """Test command and join."""
        match (joiner, word):
            case None, None:
                result = text.join(strings)
            case str(joiner), None:
                result = text.join(strings=strings, joiner=joiner)
            case None, str(word):
                result = text.join(strings=strings, word=word)
            case _:
                result = text.join(strings=strings, joiner=joiner, word=word)
        assert result == expected

    @pytest.mark.parametrize(
        ("initial", "expected"),
        [
            ("", ""),
            ("abc", "abc"),
            ("a-b", "a-b"),
            (f"a{chr(8208)}b", "a-b"),
            (f"a{chr(8211)}b", "a-b"),
            (f"{chr(8216)}your_mom{chr(8217)}", "'your_mom'"),
            ("one…two", "one...two"),
            (f"one{chr(8230)}two", "one...two"),
            ("é", "é"),  # fix() should not drop accents.
        ],
    )
    def test__fix(self, initial: str, expected: str) -> None:
        """Test fix."""
        assert text.fix(initial) == expected

    @pytest.mark.parametrize(
        ("initial", "expected"),
        [
            ("your_mom", "your_mom"),
            ("your mom", "your_mom"),
            ("your mom!", "your_mom"),
            ("your.mom", "your.mom"),
            ("your (mom)", "your__mom"),
            ("your [mom]", "your__mom"),
            ("your mom & me", "your_mom_and_me"),
            ("é", "e"),  # get_filename should drop accents
            ("your_mom...", "your_mom"),
            ("I.D.", "I.D."),
        ],
    )
    def test__get_filename(self, initial: str, expected: str) -> None:
        """Test get-filename."""
        assert text.filename_from_title(initial) == expected

    @pytest.mark.parametrize(
        ("text_input", "expected"),
        [
            ("", []),
            ("1", [1]),
            ("01", [1]),
            ("your_mom_goes_2_college", [2]),
            ("01__two3_four", [1, 3]),
            ("1a2b3c4d", [1, 2, 3, 4]),
        ],
    )
    def test__get_numbers(self, text_input: str, expected: list[int]) -> None:
        """Test get-numbers."""
        assert text.get_numbers(text_input) == expected

    @pytest.mark.parametrize(
        ("input_text", "expected"),
        [
            ("your mom", None),
            ("123e4567-e89b-12d3-a456-426614174000", "123e4567-e89b-12d3-a456-426614174000"),
            (
                "https://musicbrainz.org/artist/3630fff3-52fc-4e97-ab01-d68fd88e4135",
                "3630fff3-52fc-4e97-ab01-d68fd88e4135",
            ),
            (
                "11111111-e89b-12d3-a456-426614174000 and 22222222-e89b-12d3-a456-426614174000",
                "11111111-e89b-12d3-a456-426614174000",
            ),
        ],
    )
    def test__get_uuid(self, input_text: str, expected: str | None) -> None:
        """Test get-uuid."""
        assert text.get_uuid(input_text) == expected
