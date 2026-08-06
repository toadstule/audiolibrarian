#  Copyright (C) 2026 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Domain services: library_layout."""

from __future__ import annotations

import enum
import pathlib
from typing import TYPE_CHECKING

from audiolibrarian.common import text

if TYPE_CHECKING:
    from audiolibrarian.domain.model.release import Release
    from audiolibrarian.domain.model.track import Track
    from audiolibrarian.domain.model.values import MediumPosition


class FormatTreeName(enum.StrEnum):
    """Format tree names."""

    FLAC = enum.auto()
    M4A = enum.auto()
    MP3 = enum.auto()
    SOURCE = enum.auto()


def artist_year_album_path(release: Release) -> pathlib.Path:
    """Return the artist/year__album path.

    Args:
        release: The Release object.

    Example:
      - artist__the/1969__the_album
    """
    first_artist = release.album_artists_sort.first if release.album_artists_sort else None
    if first_artist is None:
        msg = "Unable to determine artist path without artist(s)"
        raise ValueError(msg)
    artist_dir = pathlib.Path(text.filename_from_title(first_artist))
    if release.original_year is None or release.album is None:
        msg = "Unable to determine album path without year and album"
        raise ValueError(msg)
    album_dir = pathlib.Path(text.filename_from_title(f"{release.original_year}__{release.album}"))
    return artist_dir / album_dir


def artist_year_album_disc_path(release: Release, medium_position: MediumPosition) -> pathlib.Path:
    """Return the artist/year__album/disc path.

    Args:
        release: The Release object.
        medium_position: The MediumPosition object.
    """
    if medium_position.count == 1:
        return artist_year_album_path(release)
    return artist_year_album_path(release) / f"disc{medium_position.number}"


def full_path(
    root_path: pathlib.Path, format_tree_name: FormatTreeName, release: Release, medium_position: MediumPosition
) -> pathlib.Path:
    """Return the full path for a given root path, format tree name, release, and medium position."""
    return root_path / format_tree_name.value / artist_year_album_disc_path(release, medium_position)


def track_filename(track: Track, *, suffix: str = "") -> str:
    """Return a sane filename based on track number and title.

    If suffix is included, it will be appended to the filename.
    """
    if track.title is None or track.track_number is None:
        msg = "Unable to generate a filename for Track with missing number and/or title"
        raise ValueError(msg)
    return f"{track.track_number}__{text.filename_from_title(track.title)}{suffix}"
