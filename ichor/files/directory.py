import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Type

from ichor.common.functools import (buildermethod, cached_property,
                                    classproperty)
from ichor.files.file import File, FileState
from ichor.files.path_object import PathObject

from ichor.common.io import mkdir


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

    def mkdir(self):
        mkdir(self.path)

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
                if issubclass(inst.__class__, PathObject):
                    inst.read()
            self.state = FileState.Read

    def iterdir(self):
        """alias to __iter__ in case child object overrides __iter__"""
        return self.path.iterdir()

    def __iter__(self):
        """When code iterates over an instance of a directory, it calls the pathlib iterdir() method which yields
        path objects to all directory contents."""
        return self.iterdir()


class AnnotatedDirectory(Directory, ABC):
    """Abstract method for adding a parser for a Directory that has annotated files"""

    @cached_property
    def filetypes(self) -> Dict[str, Type[File]]:
        filetypes = {}
        if hasattr(self, "__annotations__"):
            for var, type_ in self.__annotations__.items():
                if hasattr(type_, "__args__"):  # Optional
                    type_ = type_.__args__[0]

                # GJF and WFN are subclasses of File
                if issubclass(type_, File):
                    filetypes[var] = type_
        return filetypes

    @cached_property
    def dirtypes(self) -> Dict[str, Type[Directory]]:
        dirtypes = {}
        if hasattr(self, "__annotations__"):
            for var, type_ in self.__annotations__.items():
                if hasattr(type_, "__args__"):  # Optional
                    type_ = type_.__args__[0]

                # GJF and WFN are subclasses of File
                if issubclass(type_, Directory):
                    dirtypes[var] = type_
        return dirtypes

    def files(self):
        return [getattr(self, var) for var in vars(self) if isinstance(getattr(self, var), File)]

    def directories(self):
        return [getattr(self, var) for var in vars(self) if isinstance(getattr(self, var), Directory)]

    def parse(self):
        """todo: fix this docstring
        Iterate over __annotations__ which is a dictionary of {"gjf": Optional[GJF], "wfn": Optional[WFN], "ints": Optional[INTs]}
        as defined from class variables in PointsDirectory. Get the type inside the [] brackets. After that it constructs a filetypes
        dictionary containing {"gjf": GJF, "wfn": WFN} and dirtypes dictionary containing {"ints": INTs}
        """
        if not self.exists():
            return

        filetypes = self.filetypes
        dirtypes = self.dirtypes

        for f in self.path.iterdir():
            # if the content is a file. This is true for .gjf/.wfn files todo: fix this
            if f.is_file():
                for var, filetype in filetypes.items():
                    # if the suffix is either gjf or wfn, since there could be other files in the directory (such as .gau which we don't use) todo: fix this
                    if filetype.check_path(f):
                        if (
                            "parent"
                            in inspect.signature(filetype.__init__).parameters
                        ):
                            setattr(self, var, filetype(f, parent=self))
                        else:
                            setattr(self, var, filetype(f))
                        break
            # if the content is a directory. This is currently only for `*_atomicfiles` directories containing .int files todo: fix this
            elif f.is_dir():
                for var, dirtype in dirtypes.items():
                    if dirtype.check_path(f):
                        if (
                            "parent"
                            in inspect.signature(dirtype.__init__).parameters
                        ):
                            # sets the .ints attribute to INTs(path_to_directory, parent=PointDirecotry_instance) todo: fix this
                            setattr(self, var, dirtype(f, parent=self))
                        else:
                            setattr(self, var, dirtype(f))
                        break
