import shutil
from abc import ABC, abstractmethod
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ichor.common.functools import (buildermethod, called_from_hasattr,
                                    classproperty, hasattr)
from ichor.common.io import move
from ichor.common.obj import (object_getattribute, object_getdict,
                              object_hasattr, object_setattr)
from ichor.files.path_object import PathObject
from contextlib import contextmanager


class FileReadError(Exception):
    pass


class FileState(Enum):
    """An enum that is used to make it easier to check the current file state."""

    Unread = 1
    Reading = 2
    Read = 3
    Blocked = -1


class FileContentsType:
    pass


FileContents = FileContentsType()


class File(PathObject, ABC):
    """Abstract Base Class for any type of file that is used by ICHOR."""

    state: FileState = FileState.Unread

    def __init__(self, path: Union[Path, str]):
        super().__init__(path)  # initialize PathObject init
        self.state = FileState.Unread

    @buildermethod
    def read(self, *args, **kwargs) -> None:
        """Read the contents of the file. Depending on the type of file, different parts will be read in."""
        if self.path.exists() and self.state is FileState.Unread:
            self.state = FileState.Reading
            self._read_file(
                *args, **kwargs
            )  # self._read_file is different based on which type of file is being read (GJF, AIMALL, etc.)
            self.state = FileState.Read
        elif not self.path.exists() and self.state is not FileState.Blocked:
            raise FileNotFoundError(f"File with path '{self.path}' is not found on disk.")

    @abstractmethod
    def _read_file(self, *args, **kwargs):
        pass

    def move_formatted(self, dst):
        pass

    @classproperty
    @abstractmethod
    def filetype(self) -> str:
        pass

    @property
    def _file_contents(self):
        return list(self.__dir__()) + self.file_contents

    @property
    def file_contents(self) -> List[str]:
        return []

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.suffix == cls.filetype

    def move(self, dst) -> None:
        """Move the file to a new destination.

        :param dst: The new path to the file.
        """
        if dst.is_dir():
            dst /= self.path.name
        move(self.path, dst)

    def write(self, path: Optional[Path] = None):
        raise NotImplementedError(
            f"'write' method not implemented for {self.__class__.__name__}"
        )

    @contextmanager
    def block(self):
        self._save_state = self.state
        try:
            self.state = FileState.Blocked
            yield
        finally:
            self.unblock()
    

    def unblock(self):
        if self.state is FileState.Blocked:
            self.state = self._save_state


    def __getattribute__(self, item):
        """This is what gets called when accessing an attribute of an instance. Here, we check if the attribute exists or not.
        If the attribute does not exist, then read the file and update its filestate. Then try to return the value of the attribute, if
        the attribute still does not exist after reading the file, then return an AttributeError.

        One must be careful to make sure all attributes that want to be accessed lazily must be an attribute of the class and
        not to override __getattribute__ in subclasses of PathObject.

        :param item: The attribute that needs to be accessed.
        """

        # check if the attribute has value FileContents, if not read file
        try:
            if super().__getattribute__(item) is FileContents:
                self.read()
        except AttributeError:  # todo: see if we can get rid of the need for this as can cause issues if there is truly an AttributeError in self.read()
            if item in self._file_contents:
                self.read()

        # now that the file is read, return the attribute that should exist now
        try:
            return super().__getattribute__(item)
        except AttributeError:
            raise AttributeError(
                f"{object_getattribute(self, 'path')} instance of {object_getattribute(self, '__class__').__name__} has no attribute {item}"
            )

    def __getitem__(self, item):
        """Tries to return the item indexed with [] brackets. If the item does not exist and the filestate is Unread, then
        read the file and try to access the item again. If the item still does not exist, then throw a KeyError."""
        try:
            return super().__getitem__(item)
        except KeyError:
            if self.state is FileState.Unread:
                self.read()
                return self.__getitem__(item)
        raise KeyError(f"No '{item}' item found for '{self.path}'")
