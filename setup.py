#
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
from distutils.core import setup


def get_version() -> str:
    with open("audiolibrarian/__init__.py") as pkg_init:
        for line in pkg_init:
            if line.startswith("__version__"):
                return line.split('"')[1]


if __name__ == "__main__":
    setup(
        name="audiolibrarian",
        version=get_version(),
        packages=["audiolibrarian", "audiolibrarian.audiofile", "picard_src"],
        url="https://bitbucket.org/toadstule/audiolibrarian/",
        license="GNU General Public License v3.0",
        author="Steve Jibson",
        author_email="audiolibrarian@jibson.com",
        description="Audio library utilities",
        scripts=["scripts/audiolibrarian"],
        install_requires=[line.strip() for line in open("requirements.base.txt")],
    )
