import glob
import os
import subprocess

from audiolibrarian.output import Dots


def parallel(message, commands, touch=None):
    """Execute commands in parallel."""
    touch = touch or []
    with Dots(message) as d:
        for p in [subprocess.Popen(c) for c in commands]:
            d.dot()
            p.wait()
    for fn in sorted(glob.glob(os.path.join(touch, "*"))):
        subprocess.run(("touch", fn))
