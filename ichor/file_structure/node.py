from pathlib import Path


class FileNode:
    def __init__(self, name, parent):
        self.name = Path(name)
        self.parent = parent

    @property
    def path(self):
        if self.parent is None:
            return self.name
        return self.parent.path / self.name

    def __str__(self):
        return str(self.path)

    def __repr__(self):
        return str(self)
