#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Test commands."""

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
