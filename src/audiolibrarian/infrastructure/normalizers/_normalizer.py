#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Audio normalization functionality using different backends."""

from __future__ import annotations

import abc
import logging
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

import pydantic

from audiolibrarian import config

if TYPE_CHECKING:
    import pathlib

log = logging.getLogger(__name__)

T = TypeVar("T", bound=pydantic.BaseModel)


class Normalizer[T](abc.ABC):
    """Abstract base class for audio normalizers."""

    name: str
    _registry: ClassVar[dict[str, type[Normalizer[Any]]]] = {}
    _auto_normalizer: ClassVar[type[Normalizer[Any]] | None] = None
    _auto_priority: ClassVar[int] = -1

    def __init__(self, settings: T) -> None:
        """Initialize a Normalizer instance.

        Args:
            settings: The settings specific to this normalizer type.
        """
        self._settings: T = settings

    def __init_subclass__(cls, *, priority: int, available: bool) -> None:
        """Register a new normalizer."""
        super().__init_subclass__()
        if not available:
            return
        cls._registry[cls.name] = cls
        if priority > cls._auto_priority:
            cls._auto_normalizer = cls
            cls._auto_priority = priority

    @classmethod
    def factory(cls, settings: config.NormalizeSettings) -> Normalizer[Any]:
        """Create the appropriate normalizer based on settings.

        Args:
            settings: The normalization settings.

        Returns:
            An instance of the appropriate Normalizer implementation.
        """
        if settings.normalizer == "auto":
            selected_normalizer = cls._auto_normalizer.name if cls._auto_normalizer else "none"
            if selected_normalizer != "none":
                log.info("auto-selected %s for normalization", selected_normalizer)
        elif settings.normalizer in cls._registry:
            selected_normalizer = settings.normalizer
        else:
            log.warning("%s is not available; using no normalization", settings.normalizer)
            selected_normalizer = "none"
        normalizer_settings = settings.get(selected_normalizer, config.EmptySettings())
        return cls._registry[selected_normalizer](normalizer_settings)

    @abc.abstractmethod
    def normalize(self, paths: set[pathlib.Path]) -> None:
        """Normalize the given audio files.

        Args:
            paths: Set of audio file paths to normalize.

        Raises:
            Exception: If the normalization process fails.
        """
