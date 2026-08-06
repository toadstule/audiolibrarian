#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Application ports for metadata providers."""

from typing import Protocol


class MetadataProviderP(Protocol):
    """A metadata provider port."""
