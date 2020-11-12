# Copyright (C) 2020 Stephen Jibson

import subprocess
from typing import List, Tuple

from audiolibrarian.output import Dots


def parallel(message: str, commands: List[Tuple]):
    """Execute commands in parallel."""
    with Dots(message) as d:
        for p in [subprocess.Popen(c) for c in commands]:
            d.dot()
            p.wait()


def touch(paths):
    """Touch all files in a given path."""
    for p in paths:
        subprocess.run(("touch", p))
