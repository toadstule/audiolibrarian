import sys


class Dots:
    def __init__(self, message):
        self._out(message)

    def __enter__(self):
        return self

    def __exit__(self, _, __, ___):
        self._out("\n")

    def dot(self):
        self._out(".")

    @staticmethod
    def _out(message):
        sys.stdout.write(message)
        sys.stdout.flush()
