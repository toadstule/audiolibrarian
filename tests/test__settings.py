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

import importlib
import os
import pathlib
from unittest.mock import patch

import pytest
import yaml.scanner

from audiolibrarian import settings


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

    @staticmethod
    def _get_settings() -> settings.Settings:
        """Return a fresh instance of SETTINGS."""
        from audiolibrarian import settings

        importlib.reload(settings)
        return settings.SETTINGS

    def test_default_settings(self, test_env: dict[str, str], tmp_path: pathlib.Path) -> None:
        """Test that default settings are properly initialized."""
        with patch.dict(os.environ, test_env, clear=True):
            settings_ = self._get_settings()

        assert settings_.library_dir == pathlib.Path("library").resolve()
        assert settings_.work_dir == self._get_cache_home(tmp_path) / "audiolibrarian"
        assert settings_.discid_device is None
        assert settings_.normalize_gain == 5  # noqa: PLR2004
        assert settings_.normalize_preset == "radio"
        assert settings_.musicbrainz.rate_limit == 1.5  # noqa: PLR2004
        assert settings_.musicbrainz.username == ""
        assert isinstance(settings_.musicbrainz.password, settings.pydantic.SecretStr)

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
            normalize_gain: 10
            normalize_preset: album
        """

        with patch.dict(os.environ, test_env, clear=True):
            # Write the test configuration file
            config_path.write_text(test_yaml)

            # Create Settings with default YAML file location
            test_settings = self._get_settings()

            assert test_settings.library_dir == tmp_path / "Music_overridden"
            assert test_settings.work_dir == tmp_path / "test_work_overridden"
            assert test_settings.discid_device == "/dev/sr0"
            assert test_settings.musicbrainz.username == "test_user"
            assert test_settings.musicbrainz.password.get_secret_value() == "test_pass"
            assert test_settings.musicbrainz.rate_limit == 2  # noqa: PLR2004
            assert test_settings.normalize_gain == 10  # noqa: PLR2004
            assert test_settings.normalize_preset == "album"

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

        with patch.dict(os.environ, test_env, clear=True):
            # Write the test configuration file
            config_path.write_text(test_yaml)

            # Set environment variables
            os.environ["AUDIOLIBRARIAN__LIBRARY_DIR"] = str(tmp_path / "Music_env")
            os.environ["AUDIOLIBRARIAN__WORK_DIR"] = str(tmp_path / "work_env")
            os.environ["AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME"] = "test_user_env"

            # Create Settings with default YAML file location
            test_settings = self._get_settings()

            assert test_settings.library_dir == tmp_path / "Music_env"
            assert test_settings.work_dir == tmp_path / "work_env"
            assert test_settings.musicbrainz.username == "test_user_env"

    def test_invalid_yaml(self, test_env: dict[str, str], config_path: pathlib.Path) -> None:
        """Test handling of invalid YAML file."""
        invalid_yaml = "invalid: yaml: file"

        with patch.dict(os.environ, test_env, clear=True):
            # Write the invalid YAML file
            config_path.write_text(invalid_yaml)

            with pytest.raises(yaml.scanner.ScannerError):
                self._get_settings()
