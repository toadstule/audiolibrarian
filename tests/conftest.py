"""Pytest configuration and fixtures."""

#
#  Copyright (c) 2000-2025 Stephen Jibson
#
#   This file is part of audiolibrarian.
#
#   Audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#   GNU General Public License as published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   Audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#   without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#   the GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License along with audiolibrarian.
#   If not, see <https://www.gnu.org/licenses/>.
#
import os
import pathlib

import _pytest.config
import pytest


def pytest_configure(config: _pytest.config.Config) -> None:
    """Configure pytest and set up environment variables.

    This runs before any test modules are imported.
    """
    # Create a temporary directory for this test session
    cache_dir = pathlib.Path(str(config.cache.mkdir("work_dir")))
    work_dir = cache_dir / "work_dir"
    work_dir.mkdir(exist_ok=True, parents=True)

    # Set the environment variable before any imports happen
    os.environ["AUDIOLIBRARIAN__WORK_DIR"] = str(work_dir)


@pytest.fixture(scope="session")
def work_dir() -> pathlib.Path:
    """Get the path to the session's work directory."""
    return pathlib.Path(os.environ["AUDIOLIBRARIAN__WORK_DIR"])
