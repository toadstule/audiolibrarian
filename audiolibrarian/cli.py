"""Audiolibrarian command line interface."""
#  Copyright (c) 2021 Stephen Jibson
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
import argparse
import logging
import pathlib
import subprocess
import sys

from audiolibrarian import commands

log = logging.getLogger("audiolibrarian")


class CommandLineInterface:
    """Command line interface."""

    required_exe = (
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

    def __init__(self, parse_args: bool = True):
        """Initialize a CommandLineInterface handler."""
        if parse_args:
            self._args = self._parse_args()
            self.log_level = self._args.log_level

    def execute(self):
        """Execute the command."""
        log.info(f"ARGS: {self._args}")
        if not self._check_deps():
            sys.exit(1)
        for cmd in commands.commands:
            if self._args.command == cmd.command:
                if not cmd.validate_args(self._args):
                    sys.exit(2)
                cmd(self._args)
                break
        if self._args.log_level == logging.DEBUG:
            print(pathlib.Path("/proc/self/status").read_text())

    def _check_deps(self) -> bool:
        """Check that all the executables defined in REQUIRED_EXE exist on the system.

        If any of the required executables are missing, list them and return False.
        """
        missing = []
        for exe in self.required_exe:
            try:
                subprocess.run(
                    ("which", exe),
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
        parser = argparse.ArgumentParser(description="Audio Librarian")

        # global options
        parser.add_argument(
            "--log-level",
            "-l",
            choices=("CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"),
            default="ERROR",
            help="log level (default: ERROR)",
        )

        # add sub-commands and args for sub_commands
        subparsers = parser.add_subparsers(title="commands", dest="command")
        for cmd_ in commands.commands:
            # this is a total hack because argparse won't allow you to add an already
            # existing ArgumentParser as a sub-parser.
            # pylint: disable=protected-access
            if cmd_.parser:
                cmd_.parser.prog = f"{subparsers._prog_prefix} {cmd_.command}"
                subparsers._choices_actions.append(
                    subparsers._ChoicesPseudoAction(cmd_.command, (), cmd_.help)
                )
                subparsers._name_parser_map[cmd_.command] = cmd_.parser

        return parser.parse_args()
