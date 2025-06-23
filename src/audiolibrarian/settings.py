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
import logging
import pathlib
from typing import Literal

import pydantic
import pydantic_settings
import xdg_base_dirs

logger = logging.getLogger(__name__)


class MusicBrainzSettings(pydantic_settings.BaseSettings):
    """Configuration settings for MusicBrainz."""

    password: pydantic.SecretStr = pydantic.SecretStr("")
    username: str = ""
    rate_limit: pydantic.PositiveFloat = 1.5  # Seconds between requests.


class NormalizeFFmpegSettings(pydantic_settings.BaseSettings):
    """Configuration settings for ffmpeg normalization."""

    target_level: float = -13


class NormalizeWavegainSettings(pydantic_settings.BaseSettings):
    """Configuration settings for wavegain normalization."""

    gain: int = 5  # dB
    preset: Literal["album", "radio"] = "radio"


class NormalizeSettings(pydantic_settings.BaseSettings):
    """Configuration settings for audio normalization."""

    normalizer: Literal["auto", "wavegain", "ffmpeg", "none"] = "auto"
    ffmpeg: NormalizeFFmpegSettings = NormalizeFFmpegSettings()
    wavegain: NormalizeWavegainSettings = NormalizeWavegainSettings()


class Settings(pydantic_settings.BaseSettings):
    """Configuration settings for AudioLibrarian."""

    discid_device: str | None = None  # Use default device.
    library_dir: pathlib.Path = pathlib.Path("library").resolve()
    musicbrainz: MusicBrainzSettings = MusicBrainzSettings()
    normalize: NormalizeSettings = NormalizeSettings()
    work_dir: pathlib.Path = xdg_base_dirs.xdg_cache_home() / "audiolibrarian"

    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUDIOLIBRARIAN__",
        yaml_file=str(xdg_base_dirs.xdg_config_home() / "audiolibrarian" / "config.yaml"),
        frozen=True,  # Make settings immutable.
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[pydantic_settings.BaseSettings],
        init_settings: pydantic_settings.PydanticBaseSettingsSource,
        env_settings: pydantic_settings.PydanticBaseSettingsSource,
        dotenv_settings: pydantic_settings.PydanticBaseSettingsSource,
        file_secret_settings: pydantic_settings.PydanticBaseSettingsSource,
    ) -> tuple[pydantic_settings.PydanticBaseSettingsSource, ...]:
        del dotenv_settings, file_secret_settings  # Unused.
        return (
            env_settings,
            pydantic_settings.YamlConfigSettingsSource(settings_cls),
            init_settings,
        )


SETTINGS = Settings()
__all__ = ["SETTINGS"]
