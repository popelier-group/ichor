class BoolToggle:
    def __init__(self, initial_value: bool):
        self._bool = initial_value

    def __bool__(self):
        return self._bool

    def __enter__(self):
        self._bool = not self._bool

    def __exit__(self, a, b, c):
        self._bool = not self._bool
