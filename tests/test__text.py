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
