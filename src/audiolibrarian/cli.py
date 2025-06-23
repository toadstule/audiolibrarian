"""Audiolibrarian command line interface."""

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
import argparse
import logging
import pathlib
import subprocess
import sys
from typing import Final

from audiolibrarian import commands

log = logging.getLogger("audiolibrarian")


class CommandLineInterface:
    """Command line interface."""

    _REQUIRED_EXE: Final[set[str]] = {
        "cd-paranoia",
        "eject",
        "faad",
        "fdkaac",
        "flac",
        "lame",
        "mpg123",
        "sndfile-convert",
    }

    def __init__(self, *, parse_args: bool = True) -> None:
        """Initialize a CommandLineInterface handler."""
        if parse_args:
            self._args = self._parse_args()
            self.log_level = self._args.log_level

    def execute(self) -> None:
        """Execute the command."""
        log.info("ARGS: %s", self._args)
        if not self._check_deps():
            sys.exit(1)
        for cmd in commands.COMMANDS:
            if self._args.command == cmd.command:
                if not cmd.validate_args(self._args):
                    sys.exit(2)
                cmd(self._args)
                break
        if self._args.log_level == logging.DEBUG:
            print(pathlib.Path("/proc/self/status").read_text(encoding="utf-8"))

    def _check_deps(self) -> bool:
        """Check that all the executables defined in REQUIRED_EXE exist on the system.

        If any of the required executables are missing, list them and return False.
        """
        missing = []
        for exe in self._REQUIRED_EXE:
            try:
                subprocess.run(  # noqa: S602
                    f"command -v {exe}",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    check=True,
                )
            except subprocess.CalledProcessError:
                missing.append(exe)
        if missing:
            print(f"\nMissing required executable(s): {', '.join(missing)}\n")
            return False
        return True

    # noinspection PyProtectedMember
    @staticmethod
    def _parse_args() -> argparse.Namespace:
        """Parse command line arguments."""
        parser = argparse.ArgumentParser(description="audiolibrarian")

        # global options
        parser.add_argument(
            "--log-level",
            "-l",
            choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            default="ERROR",
            help="log level (default: ERROR)",
        )

        # Add sub-commands and args for sub_commands.
        subparsers = parser.add_subparsers(title="commands", dest="command")
        for cmd_ in commands.COMMANDS:
            # This is a total hack because argparse won't allow you to add an already
            # existing ArgumentParser as a sub-parser.
            if cmd_.parser:
                cmd_.parser.prog = f"{subparsers._prog_prefix} {cmd_.command}"  # noqa: SLF001
                subparsers._choices_actions.append(  # noqa: SLF001
                    subparsers._ChoicesPseudoAction(cmd_.command, (), cmd_.help)  # noqa: SLF001
                )
                subparsers._name_parser_map[cmd_.command] = cmd_.parser  # noqa: SLF001

        return parser.parse_args()


def main() -> None:
    """Execute the command line interface."""
    cli_ = CommandLineInterface()
    logging.basicConfig(level=cli_.log_level)
    logging.captureWarnings(capture=True)
    cli_.execute()
