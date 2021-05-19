import shutil
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path

from ichor.common.functools import called_from_hasattr, hasattr


class FileState(Enum):
    Unread = 1
    Reading = 2
    Read = 3


class PathObject(ABC, object):
    def __init__(self, path):
        self.path = Path(path)
        self.state = FileState.Unread

        if self.exists():
            from ichor.files.directory import Directory

            if (
                Directory in self.__class__.__bases__
                and not self.path.is_dir()
            ):
                raise TypeError(f"{self.path} is not a directory")

            from ichor.files.file import File

            if File in self.__class__.__bases__ and not self.path.is_file():
                raise TypeError(f"{self.path} is not a file")

    def exists(self) -> bool:
        return self.path.exists()

    @abstractmethod
    def move(self, dst) -> None:
        pass

    def __getattribute__(self, item):
        if not called_from_hasattr() and (
            (
                not hasattr(self, item)
                or object.__getattribute__(self, item) is None
            )
            and self.state is FileState.Unread
        ):
            self.read()

        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            raise AttributeError(
                f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute '{item}'"
            )

    def __getitem__(self, item):
        try:
            return super().__getitem__(item)
        except KeyError:
            if self.state is FileState.Unread:
                self.read()
                return self.__getitem__(item)
            raise KeyError(f"No '{item}' item found for '{self.path}'")
