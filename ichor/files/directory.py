import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type, Union

from ichor.common.functools import (buildermethod, cached_property,
                                    classproperty)
from ichor.common.io import mkdir
from ichor.files.file import File, FileState
from ichor.files.path_object import PathObject


class Directory(PathObject, ABC):
    """
    A class that implements helper methods for working with directories (which are stored on a hard drive).
    :param path: The path to a directory
    """

    def __init__(self, path: Union[Path, str]):
        PathObject.__init__(
            self, path
        )  # set path attribute for Directory instance
        self.parse()  # parse directory to find contents and setup the directory structure. THIS DOES NOT READ IN DIRECTORY CONTENTS

    @abstractmethod
    def parse(self) -> None:
        """
        Abstract method to find all relevant files within the directory.

        .. note::
            This is not reading the files just finding the paths to the files and setup the directory structure
        """
        pass

    def mkdir(self):
        """Make an empty directory at the location of the `path` attribute."""
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

    def dump(self):
        pass

    def iterdir(self):
        """alias to __iter__ in case child object overrides __iter__"""
        return self.path.iterdir()

    def __iter__(self):
        """When code iterates over an instance of a directory, it calls the pathlib iterdir() method which yields
        path objects to all directory contents."""
        return self.iterdir()


class AnnotatedDirectory(Directory, ABC):
    """Abstract method for adding a parser for a Directory that has annotated files (such as GJF, INT, WFN). For example, look at the `PointDirectory` class."""

    @cached_property
    def filetypes(self) -> Dict[str, Type[File]]:
        """Returns a dictionary of key:value pairs where the keys are the attributes and the values are the type of class these attributes are going to
        be set to. These classes are all subclassing from the `File` class. For example {'gjf': GJF,  'wfn': WFN}."""
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
        """Returns a dictionary of key:value pairs where the keys are the attributes and the values are the type of class these attributes are going to
        be set to. These classes are all subclassing from the `Directory` class. For example {'ints': INTs}."""
        dirtypes = {}
        if hasattr(self, "__annotations__"):
            for var, type_ in self.__annotations__.items():
                if hasattr(type_, "__args__"):  # Optional
                    type_ = type_.__args__[0]

                # GJF and WFN are subclasses of File
                if issubclass(type_, Directory):
                    dirtypes[var] = type_
        return dirtypes

    def files(self) -> list:
        """Return all objects which are contained in the `AnnotatedDirectory` instance and that subclass from `File` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), File)
        ]

    def directories(self) -> list:
        """Return all objects which are contained in the `AnnotatedDirectory` instance and that subclass from `Directory` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), Directory)
        ]

    def dump(self):
        for f in self.files:
            f.dump()
        for d in self.directories:
            d.dump()

    def parse(self):
        """
        Iterates over an `AnnotatedDirectory`'s contents (which could be files or other directories). If the content is a file,
        """
        if not self.exists():
            return

        filetypes = self.filetypes
        dirtypes = self.dirtypes

        for f in self.path.iterdir():

            # if the content is a file. This is true for any files (everything other than directories)
            if f.is_file():
                # iterate over the filetypes dictionary {"gjf": GJF, "wfn": WFN,......}
                for var, filetype in filetypes.items():
                    # if the suffix of the file matches the suffix of the class
                    if filetype.check_path(f):

                        # set attributes for the object which wrap around a file (such as .gjf, .wfn, etc.)
                        # if this type of file needs access to the parent (the `AnnotatedDirectory`'s path)
                        if (
                            "parent"
                            in inspect.signature(filetype.__init__).parameters
                        ):
                            setattr(self, var, filetype(f, parent=self))
                        else:
                            setattr(self, var, filetype(f))
                        break

            # if the content is a directory. This is true for any directories (everything other than files)
            elif f.is_dir():

                # iterate over the dirtypes dictionary {"ints": INTs, ....}
                for var, dirtype in dirtypes.items():
                    # checks to see if the name of the directory matches a pattern
                    if dirtype.check_path(f):
                        if (
                            "parent"
                            in inspect.signature(dirtype.__init__).parameters
                        ):
                            # sets the .ints attribute to INTs(path_to_directory, parent=PointDirecotry_instance)
                            setattr(self, var, dirtype(f, parent=self))
                        else:
                            setattr(self, var, dirtype(f))
                        break
