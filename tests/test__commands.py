"""Test commands."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
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

import pytest

# noinspection PyProtectedMember
from audiolibrarian import __version__, commands, config

test_data_path = (Path(__file__).parent / "test_data").resolve()


class TestCommands:
    """Test commands."""

    @pytest.fixture
    def settings(self) -> config.Settings:
        """Return a Settings instance."""
        return config.Settings()

    def test__version(self, capsys: pytest.CaptureFixture[str], settings: config.Settings) -> None:
        """Test version command."""
        commands.Version(args=Namespace(), settings=settings)
        output: str = capsys.readouterr().out.strip()
        assert output == f"audiolibrarian {__version__}"


class TestValidateArgs:
    """Test argument validation."""

    def test__validate_disc(self) -> None:
        """Test validate disc."""
        assert commands._validate_disc_arg(Namespace(disc=""))
        assert commands._validate_disc_arg(Namespace(disc="1/2"))
        assert commands._validate_disc_arg(Namespace(disc="1/1"))
        assert commands._validate_disc_arg(Namespace(disc="2/9"))
        assert commands._validate_disc_arg(Namespace(disc="4/50"))

        assert not commands._validate_disc_arg(Namespace(disc="1"))
        assert not commands._validate_disc_arg(Namespace(disc="a"))
        assert not commands._validate_disc_arg(Namespace(disc="a/2"))
        assert not commands._validate_disc_arg(Namespace(disc="5/4"))
        assert not commands._validate_disc_arg(Namespace(disc="0/1"))
        assert not commands._validate_disc_arg(Namespace(disc="-5/-4"))

    def test__validate_dirs(self) -> None:
        """Test directory validation."""
        exist = str(test_data_path)
        not_exist = "/does/not/exist/"
        assert commands._validate_directories_arg(Namespace(directories=[]))
        assert commands._validate_directories_arg(Namespace(directories=[str(test_data_path)]))
        assert commands._validate_directories_arg(Namespace(directories=[exist, "/"]))

        assert not commands._validate_directories_arg(Namespace(directories=[not_exist]))
        assert not commands._validate_directories_arg(Namespace(directories=[exist, not_exist]))
        assert not commands._validate_directories_arg(Namespace(directories=[__file__, "/"]))
