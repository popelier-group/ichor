import shutil
from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import Optional

from ichor.common.functools import called_from_hasattr, hasattr
from ichor.common.obj import (object_getattribute, object_getdict,
                              object_hasattr, object_setattr)


class PathObject(ABC, object):
    """An abstract base class that is used for anything that has a path (i.e. files or directories)"""

    path: Path

    def __init__(self, path):
        self.path = Path(path)

    # def exists(self):
    #     from ichor.files.directory import Directory
    #     if (
    #         Directory in self.__class__.__bases__
    #         and not self.path.is_dir()
    #     ):
    #         raise TypeError(f"{self.path} is not a directory")
    #
    #     from ichor.files.file import File
    #     if File in self.__class__.__bases__ and not self.path.is_file():
    #         raise TypeError(f"{self.path} is not a file")

    def exists(self) -> bool:
        """Determines if the path points to an existing directory or file on the storage drive."""
        return self.path.exists()

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return True

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
# <<<<<<< HEAD
# =======
#         pass
#
#     def __getattribute__(self, item):
#         """This is what gets called when accessing an attribute of an instance. Here, we check if the attribute exists or not.
#         If the attribute does not exist, then read the file and update its filestate. Then try to return the value of the attribute, if
#         the attribute still does not exist after reading the file, then return an AttributeError.
#
#         One must be careful to make sure all attributes that want to be accessed lazily must be an attribute of the class and
#         not to override __getattribute__ in subclasses of PathObject.
#
#         :param item: The attribute that needs to be accessed.
#         """
#         # print(f"getting {item}")
#
#         objhasattr = object_hasattr(self, item)
#         objattr_value = object_getattribute(self, item)
#         objattr_isnone = objattr_value is None
#         obj_state = object_getattribute(self, "state")
#         if ((objhasattr and objattr_isnone) or not objhasattr) and obj_state is FileState.Unread:
#             object_getattribute(self, "read")()
#
#         try:
#             return object_getattribute(self, item)
#         except AttributeError:
#             raise AttributeError(
#                 f"{object_getattribute(self, 'path')} instance of {object_getattribute(self, '__class__').__name__} has no attribute {item}"
#             )
#
# >>>>>>> a4dddc1b12bf905d2bc16516616608256762a3d1

