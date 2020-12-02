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

import subprocess

from audiolibrarian.output import Dots


def parallel(message: str, commands: list[tuple]):
    """Execute commands in parallel."""
    with Dots(message) as d:
        for p in [subprocess.Popen(c) for c in commands]:
            d.dot()
            p.wait()


def touch(paths):
    """Touch all files in a given path."""
    for p in paths:
        subprocess.run(("touch", p))
