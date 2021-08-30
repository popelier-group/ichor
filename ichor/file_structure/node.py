from pathlib import Path


class FileNode:
    """Class used to make directory/file management easier. Each FileNode object contains a name, which is
    the path of the directory/file (relative to current directory).
    
    :param name: The path of a file or directory
    :param parent: A directory which contains the directory/file whose path is stored in `self.name`
    """

    def __init__(self, name: str, parent: str):
        self.name = Path(name)
        self.parent = parent

    @property
    def path(self) -> Path:
        if self.parent is None:
            return self.name
        return self.parent.path / self.name

    def __str__(self) -> str:
        return str(self.path)

    def __repr__(self) -> str:
        return str(self)
