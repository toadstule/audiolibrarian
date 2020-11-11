__version__ = "0.9.0"

import subprocess

from audiolibrarian.commands import Convert, Genre, Manifest, Reconvert, Rip, Version

commands = (Convert, Genre, Manifest, Reconvert, Rip, Version)

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
