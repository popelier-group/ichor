import inspect
import re
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type, Union

from ichor.core.common.functools import cached_property
from ichor.core.common.io import mkdir, move
from ichor.core.files.file import File
from ichor.core.files.path_object import PathObject


class Directory(PathObject, ABC):
    """
    A class that implements helper methods for working with directories (which are stored on a hard drive).
    :param path: The path to a directory
    """

    def __init__(self, path: Union[Path, str]):

        super().__init__(path)
        self._parse()  # parse directory to find contents and setup the directory structure. THIS DOES NOT READ IN DIRECTORY CONTENTS

    @abstractmethod
    def _parse(self) -> None:
        """
        Abstract method to find all relevant files within the directory.

        .. note::
            This is not reading the files just finding the paths to the files and setup the directory structure
        """
        pass

    def mkdir(self):
        """Make an empty directory at the location of the `path` attribute."""
        mkdir(self.path)

    def move(self, dst: Path):
        """
        Move a directory object to a new location (a new path), modifies the `path` attribute and moves contents on disk
        :param dst: The new path of the directory
        """
        move(self.path, dst)

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
    def pathtypes(self) -> Dict[str, Type[PathObject]]:
        return {**self.filetypes, **self.dirtypes}

    @cached_property
    def filetypes(self) -> Dict[str, Type[File]]:
        """Returns a dictionary of key:value pairs where the keys are the attributes and the values are the type of class these attributes are going to
        be set to. These classes are all subclassing from the `File` class. For example {'gjf': GJF,  'wfn': WFN}."""
        filetypes = {}
        if hasattr(self, "__annotations__"):
            for var, type_ in self.__annotations__.items():
                if hasattr(
                    type_, "__args__"
                ):  # Optional typing contains a list of typings
                    type_ = type_.__args__[0]

                # GJF and WFN are subclasses of File for example
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
                if hasattr(
                    type_, "__args__"
                ):  # Optional typing contains a list of typings
                    type_ = type_.__args__[0]

                # GJF and WFN are subclasses of File
                if issubclass(type_, Directory):
                    dirtypes[var] = type_
        return dirtypes

    def files(self) -> List[File]:
        """Return all objects which are contained in the `AnnotatedDirectory` instance and that subclass from `File` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), File)
        ]

    def directories(self) -> List[Directory]:
        """Return all objects which are contained in the `AnnotatedDirectory` instance and that subclass from `Directory` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), Directory)
        ]

    def path_objects(self) -> List[PathObject]:
        """Returns a list of PathObjects corresponding to files and directories
        that are in the instance of AnnotatedDirectory."""
        return self.files() + self.directories()

    def _parse(self):
        """
        Iterates over an `AnnotatedDirectory`'s contents (which are files or other sub-directories). If the content is a file,
        then check the filetype of the file (compared to the filetype which the classes subclassing from File have). After
        the check succeeds, check if that filetype needs a parent (meaning that the filetype needs access to the parent directory
        because it needs information from parent directory). For example, an .int file needs access to the parent
        directory because it needs the whole geometry ot calculate the ALF. The same is done for directories.
        """
        if not self.exists():
            return

        for f in self.path.iterdir():
            # iterate over the filetypes dictionary {"gjf": GJF, "wfn": WFN,......}
            for var, pathtype in self.pathtypes:
                # if the suffix of the file matches the suffix of the class
                if pathtype.check_path(f):
                    # set attributes for the object which wrap around a file (such as .gjf, .wfn, etc.)
                    setattr(self, var, pathtype(f))
                    break
