from unittest import TestCase

from audiolibrarian import text


class TestText(TestCase):
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
