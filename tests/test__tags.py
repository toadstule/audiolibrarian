# Copyright (C) 2020 Stephen Jibson

from unittest import TestCase

from audiolibrarian.audiofile.tags import Tags


class TestTags(TestCase):
    def test__tags(self):
        t = Tags()
        t["a"] = "A"
        t["b"] = "B"
        t["c"] = None
        expected = {"a": "A", "b": "B"}
        self.assertDictEqual(expected, t)

    def test__tags_init(self):
        t = Tags({"a": "A", "b": "B", "c": None})
        expected = {"a": "A", "b": "B"}
        self.assertDictEqual(expected, t)

    def test__tags_list(self):
        t = Tags()
        t["a"] = "A"
        t["b"] = [None]
        t["c"] = ["c", None]
        t["d"] = ["None"]
        t["e"] = {"1": None}
        expected = {"a": "A"}
        self.assertDictEqual(expected, t)
