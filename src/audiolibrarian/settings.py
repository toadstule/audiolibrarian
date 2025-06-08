"""Configuration module for AudioLibrarian.

This module provides configuration management using pydantic-settings, supporting multiple
sources of configuration:

1. Environment Variables (highest precedence):
   - Prefix: "AUDIOLIBRARIAN__"
   - Nested fields: Use "__" as delimiter (e.g., AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME)

2. YAML Configuration File:
   - Location: $XDG_CONFIG_HOME/audiolibrarian/config.yaml
   - Supports nested structure for MusicBrainz settings

3. Default Values:
   - Defined in Settings class
   - Lowest precedence

The configuration is immutable (frozen=True) and follows XDG base directory standards for
configuration and cache locations.

Sensitive fields (like passwords) are handled using pydantic.SecretStr for security.
"""

import logging
import pathlib
from typing import Literal

import pydantic
import xdg_base_dirs
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    YamlConfigSettingsSource,
)

logger = logging.getLogger(__name__)


class MusicBrainzSettings(BaseSettings):
    """Configuration settings for MusicBrainz."""

    password: pydantic.SecretStr = pydantic.SecretStr("")
    username: str = ""
    rate_limit: pydantic.PositiveFloat = 1.5  # Seconds between requests.


class Settings(BaseSettings):
    """Configuration settings for AudioLibrarian."""

    discid_device: str | None = None  # Use default device.
    library_dir: pathlib.Path = pathlib.Path("library").resolve()
    musicbrainz: MusicBrainzSettings = MusicBrainzSettings()
    normalize_gain: int = 5  # dB
    normalize_preset: Literal["album", "radio"] = "radio"
    work_dir: pathlib.Path = xdg_base_dirs.xdg_cache_home() / "audiolibrarian"

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUDIOLIBRARIAN__",
        yaml_file=str(xdg_base_dirs.xdg_config_home() / "audiolibrarian" / "config.yaml"),
        frozen=True,  # Make settings immutable.
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        del dotenv_settings, file_secret_settings  # Unused.
        return env_settings, YamlConfigSettingsSource(settings_cls), init_settings


SETTINGS = Settings()
__all__ = ["SETTINGS"]
