"""Command execution helpers."""

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
import pathlib
import subprocess
from collections.abc import Iterable
from multiprocessing import Pool

from audiolibrarian import output


def _run_command(command: tuple[str, ...]) -> None:
    """Run a single command."""
    subprocess.run(command, check=True)  # noqa: S603


def parallel(
    message: str, commands: list[tuple[str, ...]], max_workers: int | None = None
) -> None:
    """Execute commands in parallel using multiprocessing.

    Args:
        message: Progress message to display
        commands: List of commands to execute
        max_workers: Maximum number of parallel processes (None for system default)
    """
    with output.Dots(message) as dots, Pool(max_workers) as pool:
        # Start all processes
        results = [pool.apply_async(_run_command, (command,)) for command in commands]

        # Wait for all processes to complete
        for result in results:
            result.get()  # Will raise any exceptions from the subprocess
            dots.dot()


def touch(paths: Iterable[pathlib.Path]) -> None:
    """Touch all files in a given path."""
    for path in paths:
        path.touch(exist_ok=True)
