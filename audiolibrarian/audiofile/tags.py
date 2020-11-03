# noinspection PyMissingConstructor
class Tags(dict):
    """A dict-like object that silently drops keys with None in their values.

    A key will be dropped if:
    * its value is None
    * its value is a list containing None
    * its value is a dict with None in its values
    """

    def __init__(self, *args, **kwargs):
        self.update(*args, **kwargs)

    def __setitem__(self, k, v):
        if not (
            v is None
            or (type(v) is list and (None in v or "None" in v))
            or (type(v) is dict and (None in v.values() or "None" in v.values()))
        ):
            super().__setitem__(k, v)

    def update(self, *args, **kwargs):
        for k, v in dict(*args, **kwargs).items():
            self[k] = v
