import shutil
from abc import ABC, abstractmethod

from ichor.common.functools import buildermethod, classproperty
from ichor.common.io import move
from ichor.files.path_object import FileState, PathObject


class File(PathObject, ABC):
    def __init__(self, path):
        super().__init__(path)

    @buildermethod
    def read(self, *args, **kwargs) -> None:
        if self.path.exists() and self.state is FileState.Unread:
            self.state = FileState.Reading
            self._read_file(*args, **kwargs)
            self.state = FileState.Read

    @abstractmethod
    def _read_file(self, *args, **kwargs):
        pass

    def move(self, dst):
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
