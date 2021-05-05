from abc import ABC, abstractmethod
from enum import Enum

from ichor.common.functools import buildermethod, classproperty
from ichor.common.io import move
from ichor.files.path_object import PathObject


class FileState(Enum):
    Unread = 1
    Reading = 2
    Read = 3


class File(PathObject, ABC):
    def __init__(self, path):
        super().__init__(path)
        self.state = FileState.Unread

    @buildermethod
    def read(self) -> None:
        if self.state is FileState.Unread:
            self.state = FileState.Reading
            self._read_file()
            self.state = FileState.Read

    @abstractmethod
    def _read_file(self):
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

    def __getattribute__(self, item):
        try:
            if (
                super().__getattribute__(item) is None
                and self.state is not FileState.Reading
            ):
                self.read()
        except AttributeError:
            self.read()
        return super().__getattribute__(item)
