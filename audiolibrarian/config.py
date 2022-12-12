"""Configuration."""
#
#  Copyright (c) 2022 Stephen Jibson
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
import os
import pathlib
from typing import Any, Type

import yaml

logger = logging.getLogger(__name__)


class Config(dict[str, Any]):
    """Singleton configuration object."""

    __instance: "Config" = None
    __path: pathlib.Path | None = None

    def __init__(self, config_path: pathlib.Path | str | None = None):
        """Initialize a Config instance."""
        super().__init__()
        path = self._get_config_path(config_path)
        if Config.__path is not None:
            if path != Config.__path:
                raise ValueError(
                    f"Unable to load config from {path}; already loaded from {Config.__path}"
                )
        else:
            Config.__path = path
            self._load_config()

    def __new__(cls: Type["Config"], *args: Any, **kwargs: Any) -> "Config":
        """If an instance already exists, return it; otherwise create a new instance."""
        if cls.__instance is None:
            cls.__instance = dict.__new__(cls, *args, **kwargs)
        return cls.__instance

    def dump(self) -> None:
        """Dump the config to a file."""
        with Config.__path.open("w", encoding="utf-8") as f:
            f.write("---\n")
            yaml.dump(dict(self), f, default_flow_style=False)
            f.write("\n")

    def _load_config(self) -> None:
        """Load the config files."""
        logger.info(f"Reading config from {Config.__path}")
        if Config.__path.exists():
            with Config.__path.open("r") as f:
                self.update(yaml.safe_load(f))

    @staticmethod
    def _get_config_path(config_path: pathlib.Path | str | None) -> pathlib.Path:
        """Return the config path (pathlib.Path)."""
        match config_path:
            case pathlib.Path():
                return config_path.resolve()
            case str():
                return pathlib.Path(config_path).resolve()
            case _:
                if config_env := os.getenv("CONFIG"):
                    return pathlib.Path(config_env).resolve()
                return (
                    pathlib.Path.home() / ".config" / "audiolibrarian" / "config.yaml"
                ).resolve()
