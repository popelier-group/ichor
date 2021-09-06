import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path

from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File, FileState
from ichor.files.path_object import PathObject


class Directory(PathObject, ABC):
    """
    A class that implements helper methods for working with directories (which are stored on a hard drive).
    :param path: The path to a directory
    """

    def __init__(self, path):
        PathObject.__init__(
            self, path
        )  # set path for directory instance as well as FileState to Unread
        self.parse()  # parse directory to find contents

    @abstractmethod
    def parse(self) -> None:
        """
        Abstract method to find all relevant files within the directory,
        note this is not reading the files just finding the paths to the files
        """
        pass

    def move(self, dst):
        """
        Move a directory object to a new location (a new path), modifies the `path` attribute and moves contents on disk
        :param dst: The new path of the directory
        """
        self.path.replace(dst)
        self.path = dst
        for (
            f
        ) in (
            self.path.iterdir()
        ):  # need to use iterdir in case object overrides __iter__
            if f.is_file():
                fdst = self.path / f"{self.path.name}{f.suffix}"
                f.replace(fdst)
            else:
                if "_atomicfiles" in f.name:
                    from ichor.globals import GLOBALS

                    ddst = Path(
                        re.sub(
                            rf"{GLOBALS.SYSTEM_NAME}\d+_atomicfiles",
                            f"{self.path.name}_atomicfiles",
                            str(f),
                        )
                    )
                    ddst = self.path / ddst.name
                    f.replace(ddst)

    @buildermethod
    def read(self) -> "Directory":
        """Read a directory and all of its contents and store information that ICHOR needs to function (such as .wfn or .int information that is needed.)
        If an attribute such as a gjf's energy is being accessed, but the file has not been read yet, the file will be read in first and then the attribute
        can be returned if it has been successfully read. This method heavily ties in with accessing attributes of `File` objects, since these `File` objects
        are all encapsulated by a `Directory` object."""
        if self.state is FileState.Unread:
            self.state = FileState.Reading
            for var in vars(self):
                inst = getattr(self, var)
                if isinstance(inst, (File, Directory)):
                    inst.read()
            self.state = FileState.Read

    @classproperty
    @abstractmethod
    def dirpattern(self):
        pass

    def iterdir(self):
        """alias to __iter__ in case child object overrides __iter__"""
        return self.path.iterdir()

    def __iter__(self):
        """When code iterates over an instance of a directory, it calls the pathlib iterdir() method which yields
        path objects to all directory contents."""
        return self.iterdir()
