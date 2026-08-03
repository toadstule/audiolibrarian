#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Miscellaneous tests."""

import pytest

from audiolibrarian.entrypoints import cli


class TestMisc:
    """Test miscellaneous functions."""

    @pytest.fixture(scope="class")
    @classmethod
    def cli_(cls) -> cli.CommandLineInterface:
        """Return a cli instance."""
        return cli.CommandLineInterface(parse_args=False)

    def test__check_deps_true(self, cli_: cli.CommandLineInterface) -> None:
        """Test dependency checker."""
        # noinspection PyFinal
        cli_._REQUIRED_EXE = {"ls", "ps"}  # type: ignore[misc]
        assert cli_._check_deps()

    def test__check_deps_false(self, cli_: cli.CommandLineInterface) -> None:
        """Test dependency checker."""
        # noinspection PyFinal
        cli_._REQUIRED_EXE = {"your_mom_goes_to_college"}  # type: ignore[misc]
        assert not cli_._check_deps()
