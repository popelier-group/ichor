import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from ichor.common.functools import called_from_hasattr, hasattr


class FileState(Enum):
    # matt_todo: Not sure what Blocked is used for as it is a new addition. Does it mean you can't read the file and where would that be useful?
    """An enum that is used to make it easier to check the current file state."""
    Unread = 1
    Reading = 2
    Read = 3
    Blocked = -1


class PathObject(ABC, object):
    """An abstract base class that is used for anything that has a path (i.e. files or directories)"""
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
        """Determines if the path points to an existing directory or file on the storage drive."""
        return self.path.exists()

    @contextmanager
    def block(self):
        # matt_todo: What new has been added that needs to have blocked files? Don't know when blocking files is needed
        saved_state = self.state
        self.state = FileState.Blocked
        yield
        self.state = saved_state

    @abstractmethod
    def move(self, dst) -> None:
        """An abstract method that subclasses need to implement. This is used to move files around."""
        pass

    def __getattribute__(self, item):
        # matt_todo: can't __getattr_ be used here because it gets called after __getattribute__ fails to return the attribute?
        """This is what gets called when accessing an attribute of an instance. Here, we check if the attribute exists or not.
        If the attribute does not exist, then read the file and update its filestate. Then try to return the value of the attribute, if
        the attribute still does not exist after reading the file, then return an AttributeError.
        
        :param item: The attribute that needs to be accessed.
        """

        # matt_todo: can you put an example in the docstring for when this would occur.
        if not called_from_hasattr() and (
            (
                not hasattr(self, item)
                or object.__getattribute__(self, item) is None
            )
            and self.state is FileState.Unread
            and not self.state is FileState.Blocked
        ):
            self.read()

        try:
            return object.__getattribute__(self, item)
        except AttributeError:
            raise AttributeError(
                f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute '{item}'"
            )

    def __getitem__(self, item):
        """ Tries to return the item indexed with [] brackets. If the item does not exist and the filestate is Unread, then
        read the file and try to access the item again. If the item still does not exist, then throw a KeyError."""
        try:
            return super().__getitem__(item)
        except KeyError:
            if self.state is FileState.Unread:
                self.read()
                return self.__getitem__(item)
            raise KeyError(f"No '{item}' item found for '{self.path}'")
