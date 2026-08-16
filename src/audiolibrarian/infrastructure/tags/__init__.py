#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Tag gateway adapters - FLAC, M4A, MP3 taggers."""

import pathlib

from audiolibrarian.application.ports.tag_gateway import TagGatewayP
from audiolibrarian.infrastructure.tags import flac, m4a, mp3, tag_gateway

_ = (flac, m4a, mp3)


def create_tag_gateway(filepath: pathlib.Path) -> TagGatewayP:
    """Create a TagGateway object based on the file extension."""
    return tag_gateway.TagGateway.factory(filepath)
