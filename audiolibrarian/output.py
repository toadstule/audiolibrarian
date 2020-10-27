import sys


class Dots:
    """Context Manager that outputs a message, and dots...

    Example:
        with Dots("Please wait...") as d:
            for _ in range(10):
                time.sleep(1)  # or better, actually do some work here instead
                d.dot()
    """
    def __init__(self, message: str):
        self._out(message)

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self._out("\n")

    def dot(self) -> None:
        """Output a dot."""
        self._out(".")

    @staticmethod
    def _out(message: str) -> None:
        sys.stdout.write(message)
        sys.stdout.flush()
