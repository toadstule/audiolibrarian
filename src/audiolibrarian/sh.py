#  Copyright (C) 2020-2025 Stephen T. Jibson.
#  SPDX-License-Identifier: GPL-3.0-only

"""Command execution helpers."""

import pathlib
import subprocess
from collections.abc import Iterable
from multiprocessing import Pool

from audiolibrarian import output


def _run_command(command: tuple[str, ...]) -> None:
    """Run a single command."""
    subprocess.run(command, check=True)  # noqa: S603


def parallel(message: str, commands: list[tuple[str, ...]], max_workers: int | None = None) -> None:
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
