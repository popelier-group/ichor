from abc import ABC, abstractmethod

from ichor.common.io import move
from ichor.files.path_object import PathObject
from ichor.common.functools import classproperty


class File(PathObject, ABC):
    def __init__(self, path):
        super().__init__(path)

    @abstractmethod
    def read(self) -> None:
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
