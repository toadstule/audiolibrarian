"""Pytest configuration and fixtures."""

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
