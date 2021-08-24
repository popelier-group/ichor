import shutil
from abc import ABC, abstractmethod

from ichor.common.functools import buildermethod, classproperty
from ichor.common.io import move
from ichor.files.path_object import FileState, PathObject


class File(PathObject, ABC):
    """Abstract Base Class for any type of file that is used by ICHOR."""
    def __init__(self, path):
        super().__init__(path)  # initialize PathObject init

    @buildermethod
    def read(self, *args, **kwargs) -> None:
        """Read the contents of the file. Depending on the type of file, different parts will be read in."""
        if self.path.exists() and self.state is FileState.Unread:
            self.state = FileState.Reading
            self._read_file(*args, **kwargs) # self._read_file is different based on which type of file is being read (GJF, AIMALL, etc.)
            self.state = FileState.Read

    @abstractmethod
    def _read_file(self, *args, **kwargs):
        pass

    def move(self, dst) -> None:
        # matt_todo: There are two move methods defined here. (see the other one at the bottom.)
        """Move the file to a new destination.

        :param dst: The new path to the file.
        """
        self.path.replace(dst)
        self.path = dst

    def move_formatted(self, dst):
        pass

    @classproperty
    @abstractmethod
    def filetype(self) -> str:
        pass

    def write(self):
        raise NotImplementedError(
            f"'write' method not implemented for {self.__class__.__name__}"
        )

    def move(self, dst):
        if dst.is_dir():
            dst /= self.path.name
        move(self.path, dst)
