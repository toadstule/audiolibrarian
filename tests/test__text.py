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

    def test__fix(self):
        self.assertEqual("", text.fix(""))
        self.assertEqual("abc", text.fix("abc"))
        self.assertEqual("a-b", text.fix("a-b"))
        self.assertEqual("a-b", text.fix(f"a{chr(8208)}b"))
        self.assertEqual("a-b", text.fix(f"a{chr(8211)}b"))
        self.assertEqual("'your_mom'", text.fix(f"{chr(8216)}your_mom{chr(8217)}"))
        self.assertEqual("one...two", text.fix("one…two"))
        self.assertEqual("one...two", text.fix(f"one{chr(8230)}two"))

    def test__get_filename(self):
        self.assertEqual("your_mom", text.get_filename("your_mom"))
        self.assertEqual("your_mom", text.get_filename("your mom"))
        self.assertEqual("your_mom", text.get_filename("your mom!"))
        self.assertEqual("your.mom", text.get_filename("your.mom"))
        self.assertEqual("your__mom", text.get_filename("your (mom)"))
        self.assertEqual("your__mom", text.get_filename("your [mom]"))
        self.assertEqual("your_mom_and_me", text.get_filename("your mom & me"))

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
