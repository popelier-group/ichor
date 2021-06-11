from pathlib import Path


class MutablePath:
    def __init__(self, path: Path):
        self.path = path
