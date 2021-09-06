import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path

from ichor.common.functools import called_from_hasattr, hasattr


class FileState(Enum):
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
        """Calling `block` converts the current state to FileState.Blocked, this means that the file
        cannot be read, once called again or the context manager is exited, the state is reverted to
        state previous to calling `block`. This may be useful in case one wants to avoid possible
        recursive loops from the __getattr__ in PathObject or to optimise attribute accessing if the
        attribute does not need to be read from a file."""
        saved_state = self.state
        self.state = FileState.Blocked
        yield
        self.state = saved_state

    @abstractmethod
    def move(self, dst) -> None:
        """An abstract method that subclasses need to implement. This is used to move files around."""
        pass

    def __getattribute__(self, item):
        """This is what gets called when accessing an attribute of an instance. Here, we check if the attribute exists or not.
        If the attribute does not exist, then read the file and update its filestate. Then try to return the value of the attribute, if
        the attribute still does not exist after reading the file, then return an AttributeError.

        One must be careful to make sure all attributes that want to be accessed lazily must be an attribute of the class and
        not to override __getattribute__ in subclasses of PathObject.

        :param item: The attribute that needs to be accessed.
        """

        # As hasattr calls __getattribute__, one must check whether __getattribute__ is being
        # called from hasattr to avoid an infinite recurssive loop
        if not called_from_hasattr() and (
            (
                # reading the file may set attributes which aren't currently defined
                not hasattr(self, item)
                # subclasses attributes that want to be read lazily should be initialised to None
                or object.__getattribute__(self, item) is None
            )
            # only read if unread otherwise we have already tried looking for the attribute and need to throw an error
            and self.state is FileState.Unread
            # new addition to allow blocking of file reading
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
        """Tries to return the item indexed with [] brackets. If the item does not exist and the filestate is Unread, then
        read the file and try to access the item again. If the item still does not exist, then throw a KeyError."""
        try:
            return super().__getitem__(item)
        except KeyError:
            if self.state is FileState.Unread:
                self.read()
                return self.__getitem__(item)
            raise KeyError(f"No '{item}' item found for '{self.path}'")
