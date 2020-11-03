class Tags(dict):

    # noinspection PyMissingConstructor
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
