__version__ = "0.13.1"

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

from audiolibrarian.commands import Convert, Genre, Manifest, Reconvert, Rename, Rip, Version

commands = (Convert, Genre, Manifest, Reconvert, Rename, Rip, Version)

REQUIRED_EXE = (
    "cd-paranoia",
    "eject",
    "faad",
    "fdkaac",
    "flac",
    "lame",
    "mpg123",
    "sndfile-convert",
    "wavegain",
)


def check_deps() -> bool:
    """Check that all of the executables defined in REQUIRED_EXE exist on the system.

    If any of the required executables are missing, list them and return False.
    """
    missing = []
    for exe in REQUIRED_EXE:
        r = subprocess.run(("which", exe), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        if r.returncode:
            missing.append(exe)
    if missing:
        print(f"\nMissing required executable(s): {', '.join(missing)}\n")
        return False
    return True
