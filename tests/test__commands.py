"""Test commands."""

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
from argparse import Namespace
from pathlib import Path
from unittest import TestCase

# noinspection PyProtectedMember
from audiolibrarian import commands
from tests.helpers import captured_output

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestCommands(TestCase):
    """Test commands."""

    def test__version(self) -> None:
        """Test version command."""
        from audiolibrarian import __version__

        with captured_output() as (out, err):
            commands.Version(Namespace())
            output = out.getvalue().strip()
            self.assertEqual(f"audiolibrarian {__version__}", output)


class TestValidateArgs(TestCase):
    """Test argument validation."""

    def test__validate_disc(self) -> None:
        """Test validate disc."""
        self.assertTrue(commands._validate_disc_arg(Namespace(disc="")))  # noqa: SLF001
        self.assertTrue(commands._validate_disc_arg(Namespace(disc="1/2")))  # noqa: SLF001
        self.assertTrue(commands._validate_disc_arg(Namespace(disc="1/1")))  # noqa: SLF001
        self.assertTrue(commands._validate_disc_arg(Namespace(disc="2/9")))  # noqa: SLF001
        self.assertTrue(commands._validate_disc_arg(Namespace(disc="4/50")))  # noqa: SLF001

        self.assertFalse(commands._validate_disc_arg(Namespace(disc="1")))  # noqa: SLF001
        self.assertFalse(commands._validate_disc_arg(Namespace(disc="a")))  # noqa: SLF001
        self.assertFalse(commands._validate_disc_arg(Namespace(disc="a/2")))  # noqa: SLF001
        self.assertFalse(commands._validate_disc_arg(Namespace(disc="5/4")))  # noqa: SLF001
        self.assertFalse(commands._validate_disc_arg(Namespace(disc="0/1")))  # noqa: SLF001
        self.assertFalse(commands._validate_disc_arg(Namespace(disc="-5/-4")))  # noqa: SLF001

    def test__validate_dirs(self) -> None:
        """Test directory validation."""
        exist = str(test_data_path)
        not_exist = "/does/not/exist/"
        self.assertTrue(commands._validate_directories_arg(Namespace(directories=[])))  # noqa: SLF001
        self.assertTrue(
            commands._validate_directories_arg(Namespace(directories=[str(test_data_path)]))  # noqa: SLF001
        )
        self.assertTrue(commands._validate_directories_arg(Namespace(directories=[exist, "/"])))  # noqa: SLF001

        self.assertFalse(commands._validate_directories_arg(Namespace(directories=[not_exist])))  # noqa: SLF001
        self.assertFalse(
            commands._validate_directories_arg(Namespace(directories=[exist, not_exist]))  # noqa: SLF001
        )
        self.assertFalse(
            commands._validate_directories_arg(Namespace(directories=[__file__, "/"]))  # noqa: SLF001
        )
