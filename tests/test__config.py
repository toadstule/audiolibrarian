"""Tests for the Settings class.

These tests verify that settings are loaded correctly from various sources:
- Default values
- YAML configuration file
- Environment variables
- Proper override order (env > yaml > defaults)

The tests use a temporary directory structure to simulate XDG base directories:
- XDG_CONFIG_HOME/audiolibrarian/config.yaml
- XDG_CACHE_HOME/audiolibrarian/

All tests use pytest fixtures to ensure proper environment isolation and cleanup.
"""

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
import importlib
import os
import pathlib
from unittest.mock import patch

import pydantic
import pytest
import yaml.scanner

from audiolibrarian import config


class TestSettings:
    """Test the Settings class."""

    @pytest.fixture
    def config_path(self, tmp_path: pathlib.Path) -> pathlib.Path:
        """Return a temporary configuration directory."""
        config_path = self._get_config_home(tmp_path) / "audiolibrarian" / "config.yaml"
        config_path.parent.mkdir(parents=True, exist_ok=True)
        return config_path

    @pytest.fixture
    def test_env(self, tmp_path: pathlib.Path) -> dict[str, str]:
        """Return a set of environment variables for testing."""
        return {
            "HOME": str(tmp_path),
            "XDG_CACHE_HOME": str(self._get_cache_home(tmp_path)),
            "XDG_CONFIG_HOME": str(self._get_config_home(tmp_path)),
        }

    @staticmethod
    def _get_cache_home(tmp_path: pathlib.Path) -> pathlib.Path:
        """Return a temporary cache home path."""
        return tmp_path / "audiolibrarian_cache"

    @staticmethod
    def _get_config_home(tmp_path: pathlib.Path) -> pathlib.Path:
        """Return a temporary config home path."""
        return tmp_path / "audiolibrarian_config"

    def test_default_settings(self, test_env: dict[str, str], tmp_path: pathlib.Path) -> None:
        """Test that default settings are properly initialized."""
        with patch.dict(os.environ, test_env, clear=True):
            importlib.reload(config)
            settings = config.Settings()

        assert settings.library_dir == pathlib.Path("library").resolve()
        assert settings.work_dir == self._get_cache_home(tmp_path) / "audiolibrarian"
        assert settings.discid_device is None
        assert settings.normalize.normalizer == "auto"
        assert settings.normalize.wavegain.gain == 5  # noqa: PLR2004
        assert settings.normalize.wavegain.preset == "radio"
        assert settings.normalize.ffmpeg.target_level == -13  # noqa: PLR2004
        assert settings.musicbrainz.rate_limit == 1.5  # noqa: PLR2004
        assert settings.musicbrainz.username == ""
        assert isinstance(settings.musicbrainz.password, pydantic.SecretStr)

    def test_yaml_config_loading(
        self, test_env: dict[str, str], tmp_path: pathlib.Path, config_path: pathlib.Path
    ) -> None:
        """Test loading settings from a YAML file."""
        test_yaml = f"""---
            library_dir: '{tmp_path / "Music_overridden"}'
            work_dir: '{tmp_path / "test_work_overridden"}'
            discid_device: /dev/sr0
            musicbrainz:
                username: test_user
                password: test_pass
                rate_limit: 2
            normalize:
                normalizer: wavegain
                wavegain:
                    gain: 10
                    preset: album
                ffmpeg:
                    target_level: -14
        """
        # Write the test configuration file
        config_path.write_text(test_yaml)

        with patch.dict(os.environ, test_env, clear=True):
            # Create Settings with default YAML file location
            importlib.reload(config)
            test_settings = config.Settings()

        assert test_settings.library_dir == tmp_path / "Music_overridden"
        assert test_settings.work_dir == tmp_path / "test_work_overridden"
        assert test_settings.discid_device == "/dev/sr0"
        assert test_settings.musicbrainz.username == "test_user"
        assert test_settings.musicbrainz.password.get_secret_value() == "test_pass"
        assert test_settings.musicbrainz.rate_limit == 2  # noqa: PLR2004
        assert test_settings.normalize.wavegain.gain == 10  # noqa: PLR2004
        assert test_settings.normalize.wavegain.preset == "album"
        assert test_settings.normalize.ffmpeg.target_level == -14  # noqa: PLR2004

    def test_env_variable_override(
        self, test_env: dict[str, str], tmp_path: pathlib.Path, config_path: pathlib.Path
    ) -> None:
        """Test that environment variables override YAML settings."""
        test_yaml = f"""---
            library_dir: '{tmp_path / "Music_yaml"}'
            work_dir: '{tmp_path / "work_yaml"}'
            musicbrainz:
                username: test_user_yaml
        """
        # Write the test configuration file
        config_path.write_text(test_yaml)

        with patch.dict(
            os.environ,
            test_env
            | {
                "AUDIOLIBRARIAN__LIBRARY_DIR": str(tmp_path / "Music_env"),
                "AUDIOLIBRARIAN__WORK_DIR": str(tmp_path / "work_env"),
                "AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME": "test_user_env",
                "AUDIOLIBRARIAN__NORMALIZE__NORMALIZER": "ffmpeg",
                "AUDIOLIBRARIAN__NORMALIZE__FFMPEG__TARGET_LEVEL": "-16",
            },
            clear=True,
        ):
            # Create Settings with default YAML file location
            test_settings = config.Settings()

        assert test_settings.library_dir == tmp_path / "Music_env"
        assert test_settings.work_dir == tmp_path / "work_env"
        assert test_settings.musicbrainz.username == "test_user_env"
        assert test_settings.normalize.normalizer == "ffmpeg"
        assert test_settings.normalize.ffmpeg.target_level == -16  # noqa: PLR2004

    def test_invalid_yaml(self, test_env: dict[str, str], config_path: pathlib.Path) -> None:
        """Test handling of invalid YAML file."""
        invalid_yaml = "invalid: yaml: file"
        # Write the invalid YAML file
        config_path.write_text(invalid_yaml)

        with patch.dict(os.environ, test_env, clear=True):
            importlib.reload(config)
            with pytest.raises(yaml.scanner.ScannerError):
                config.Settings()
