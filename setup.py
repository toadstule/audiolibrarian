# Copyright (C) 2020 Stephen Jibson

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
        packages=["audiolibrarian", "audiolibrarian.audiofile"],
        url="https://bitbucket.org/toadstule/audiolibrarian/",
        license="GNU General Public License v3.0",
        author="Steve Jibson",
        author_email="audiolibrarian@jibson.com",
        description="Audio library utilities",
        scripts=["scripts/audiolibrarian"],
        install_requires=[line.strip() for line in open("requirements_base.txt")],
    )
