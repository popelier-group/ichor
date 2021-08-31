from pathlib import Path
from typing import Optional


class FileNode:
    """Class used to make directory/file management easier. Each FileNode object contains a name, which is
    the path of the directory/file (relative to current directory).

    :param name: The path of a file or directory
    :param parent: A directory which contains the directory/file whose path is stored in `self.name`
    """

    def __init__(self, name: str, parent: Optional['FileNode']):
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


class FileTree(dict):
    """A dictionary that contains key:value pairs `_id`:FileNode(name,parent). This is the base class that the `FileStructure` class inherits from.
    See `FileStructure` for more details.
    """

    def add(self, name: str, _id: str, parent: str = None) -> None:
        """
        Adds a new key:value pair of _id:FileNode(name) to the file structure of ICHOR.

        For example doing: `self.add("SAMPLE_POOL", "sample_pool")` would add a key:value pair with key=sample_pool and value=FileNode(SAMPLE_POOL)
        If a parent directory exists, then `self.add("SAMPLE_POOL", "sample_pool", parent="PARENT_DIR_NAME")` will give a key:value pair with
        key=`sample_pool` and value=`FileNode(SAMPLE_POOL, "PARENT_DIR_NAME")`
        """
        if parent is not None:
            parent = super().__getitem__(parent)
        self[_id] = FileNode(name, parent)

    def __getitem__(self, _id) -> Path:
        """ Get the Path corresponding to the given _id

        :param _id: A string used as a key, whose cossesponding value is a Path object. Example: `training_set` key returns the `TRAINING_SET` directory path
        """
        return super().__getitem__(_id).path