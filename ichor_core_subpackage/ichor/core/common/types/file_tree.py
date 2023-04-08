from enum import auto, Enum
from pathlib import Path
from typing import Optional


class WrongFileType(ValueError):
    pass


class FileType(Enum):
    File = auto()
    Directory = auto()

    @classmethod
    def check(cls, path: Path):
        if cls is FileType.File and not path.is_file():
            raise WrongFileType(
                f"Expected type {FileType.File.name}, Path {path} is type {FileType.Directory.name}"
            )
        if cls is FileType.Directory and not path.is_dir():
            raise WrongFileType(
                f"Expected type {FileType.Directory.name}, Path {path} is type {FileType.File.name}"
            )


class FileNode:
    """Class used to make directory/file management easier.
    Each FileNode object contains a name, which is
    the path of the directory/file (relative to current directory).

    :param name: The path of a file or directory
    :param parent: A directory which contains the directory/file whose path is stored in `self.name`
    """

    def __init__(
        self,
        name: str,
        parent: Optional["FileNode"],
        type_: Optional[FileType] = None,
        description: Optional[str] = None,
    ):
        self.name = Path(name)
        self.parent = parent
        self.type_ = type_ if type_ is not None else FileType.Directory
        self.description = description if description else " "

    @property
    def path(self) -> Path:
        if self.parent is None:
            return self.name
        path = self.parent.path / self.name
        if path.exists():
            self.type_.check(path)
        return path

    def __str__(self) -> str:
        return f" Path: {str(self.path)}\n Type: {self.type_}\n Description: {self.description}\n"

    def __repr__(self) -> str:
        return str(self)


class FileTree(dict):
    """A dictionary that contains key:value pairs `_id`:FileNode(name,parent).

    This class which is used to create a file structure (a tree of directory and files) where some
    commonly used directories can be accessed easily. It makes it easier to find
    the full paths of files and directories (which could be subdirectories).
    Then the full path of a directory can be obtained by doing:

    `file_structure_instance["file_or_dir"]`.

    For example you can add a `SCRIPTS` directory to a FileTree like so

    FILE_STRUCTURE.add(
        'SCRIPTS',
        "scripts",
        type_=FileType.Directory,
        description="directory with scripts"

    To get the `SCRIPTS` directory you can do:

    `self.ichor.hpc.global_variables.FileStructure["scripts"]` to get the SCRIPTS directory path.

    Because a `Path` object is returned by the above code (see the `FileNode` class),
    it makes it possible to write code like

    `if self.ichor.hpc.global_variables.FILE_STRUCTURE["scripts"].exists():`

    where the `exists()` method can be called because `self.ichor.hpc.global_variables.FILE_STRUCTURE["scripts"]`
    is a `pathlib.Path` object
    """

    # type_ is an optional string that can be typed in to indicate a file or directory.
    def add(
        self,
        name: str,
        _id: str,
        parent: str = None,
        type_: Optional[FileType] = None,
        description: Optional[str] = None,
    ):
        """
        Adds a new key:value pair of _id:FileNode(name) to the file structure of ICHOR.

        For example doing: `self.add("SAMPLE_POOL", "sample_pool")`
        would add a key:value pair with key=sample_pool and value=FileNode(SAMPLE_POOL)
        If a parent directory exists, then `self.add("SAMPLE_POOL", "sample_pool", parent="PARENT_DIR_NAME")`
        will give a key:value pair with key=`sample_pool` and value=`FileNode(SAMPLE_POOL, "PARENT_DIR_NAME")`
        """
        # the parent is the internal reference string such as
        # training_set, which then gets converted into a path in the __getitem__ method
        if parent is not None:
            parent = super().__getitem__(parent)
        self[_id] = FileNode(name, parent, type_, description)

    def __getitem__(self, _id) -> Path:
        """Get the Path corresponding to the given _id

        :param _id: A string used as a key, whose cossesponding value is a Path object.
            Example: `training_set` key returns the `TRAINING_SET` directory path
        """
        return super().__getitem__(_id).path

    def __str__(self) -> str:

        return "\n".join(["\n".join((f"{key}", str(val))) for key, val in self.items()])
