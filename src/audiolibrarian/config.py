"""Configuration module for AudioLibrarian.

This module provides configuration management using pydantic-settings, supporting multiple
sources of configuration:

1. Environment Variables (highest precedence):
   - Prefix: "AUDIOLIBRARIAN__"
   - Nested fields: Use "__" as delimiter (e.g., AUDIOLIBRARIAN__MUSICBRAINZ__USERNAME)

2. TOML Configuration File:
   - Location: $XDG_CONFIG_HOME/audiolibrarian/config.toml
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
import argparse
import logging
import pathlib
from typing import Annotated, Final, Literal

import pydantic
import pydantic_settings
import xdg_base_dirs

CONFIG_PATH: Final[pathlib.Path] = (
    xdg_base_dirs.xdg_config_home() / "audiolibrarian" / "config.toml"
)

logger = logging.getLogger(__name__)

ExpandedPath = Annotated[
    pathlib.Path,
    pydantic.AfterValidator(lambda v: v.expanduser()),
]


class EmptySettings(pydantic.BaseModel):
    """Empty settings."""


class MusicBrainzSettings(pydantic.BaseModel):
    """Configuration settings for MusicBrainz."""

    password: pydantic.SecretStr = pydantic.SecretStr("")
    username: str = ""
    rate_limit: pydantic.PositiveFloat = 1.5  # Seconds between requests.
    work_dir: ExpandedPath = xdg_base_dirs.xdg_cache_home() / "audiolibrarian"


class NormalizeFFmpegSettings(pydantic.BaseModel):
    """Configuration settings for ffmpeg normalization."""

    target_level: float = -13


class NormalizeWavegainSettings(pydantic.BaseModel):
    """Configuration settings for wavegain normalization."""

    gain: int = 5  # dB
    preset: Literal["album", "radio"] = "radio"


class NormalizeSettings(pydantic.BaseModel):
    """Configuration settings for audio normalization."""

    normalizer: Literal["auto", "wavegain", "ffmpeg", "none"] = "auto"
    ffmpeg: NormalizeFFmpegSettings = NormalizeFFmpegSettings()
    wavegain: NormalizeWavegainSettings = NormalizeWavegainSettings()


class Settings(pydantic_settings.BaseSettings):
    """Configuration settings for AudioLibrarian."""

    discid_device: str = ""  # Use default device.
    library_dir: ExpandedPath = pathlib.Path("library").resolve()
    musicbrainz: MusicBrainzSettings = MusicBrainzSettings()
    normalize: NormalizeSettings = NormalizeSettings()
    work_dir: ExpandedPath = xdg_base_dirs.xdg_cache_home() / "audiolibrarian"

    model_config = pydantic_settings.SettingsConfigDict(
        env_nested_delimiter="__",
        env_prefix="AUDIOLIBRARIAN__",
        toml_file=str(CONFIG_PATH),
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
        """Customize settings sources."""
        del dotenv_settings, file_secret_settings  # Unused.
        return (
            init_settings,  # Used for tests.
            env_settings,
            pydantic_settings.TomlConfigSettingsSource(settings_cls),
        )


class ConfigManager:
    """Manage AudioLibrarian configuration.

    This class handles all configuration-related operations including creating,
    reading, and managing the configuration file.
    """

    def __init__(self, args: argparse.Namespace) -> None:
        """Initialize and execute the ConfigManager."""
        self._config_path = CONFIG_PATH
        print(f"Config file location: {self._config_path}")
        if args.init:
            if self._config_path.exists():
                print("Config file already exists")
                return
            self.init_config_file()
            print("Created new config file")
            return
        if self._config_path.exists():
            print("\n=== Config file contents ===")
            print(self._config_path.read_text(encoding="utf-8"))
            return
        print("Config file does not exist. Use '--init' to create it.")

    def init_config_file(self) -> None:
        """Initialize a new config file with default values.

        The config file will be created at the location specified by self._config_path.
        If the parent directory doesn't exist, it will be created.

        Raises:
            FileExistsError: If the config file already exists.
            OSError: If there's an error creating the file or directories.
            FileNotFoundError: If the template file cannot be found.
        """
        # Create the config directory if it doesn't exist
        self._config_path.parent.mkdir(parents=True, exist_ok=True)

        # Get the directory where this file is located
        template_dir = pathlib.Path(__file__).parent / "templates"
        template_file = template_dir / self._config_path.name

        # Read the template and write to the config file
        self._config_path.write_text(template_file.read_text(encoding="utf-8"), encoding="utf-8")
