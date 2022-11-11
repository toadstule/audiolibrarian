"""Command execution helpers."""
import subprocess

from audiolibrarian import output

#  Copyright (c) 2020 Stephen Jibson
#
#  This file is part of audiolibrarian.
#
#  audiolibrarian is free software: you can redistribute it and/or modify it under the terms of the
#  GNU General Public License as published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  audiolibrarian is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY;
#  without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See
#  the GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License along with audiolibrarian.
#  If not, see <https://www.gnu.org/licenses/>.
#


def parallel(message: str, commands: list[tuple[str, ...]]):
    """Execute commands in parallel."""
    with output.Dots(message) as dots:
        for command in commands:
            with subprocess.Popen(command) as proc:
                dots.dot()
                proc.wait()


def touch(paths):
    """Touch all files in a given path."""
    for path in paths:
        subprocess.run(("touch", path), check=False)
