class BoolToggle:
    def __init__(self):
        _bool = False

    def __bool__(self):
        return self._bool

    def __enter__(self):
        self._bool = True

    def __exit__(self, a, b, c):
        self._bool = False
