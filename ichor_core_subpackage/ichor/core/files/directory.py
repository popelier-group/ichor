from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Type, Union

from ichor.core.common.functools import cached_property
from ichor.core.common.io import mkdir, move
from ichor.core.common.sorting.natsort import ignore_alpha, natsorted
from ichor.core.files.file import File
from ichor.core.files.optional_content import OptionalContent
from ichor.core.files.path_object import PathObject


class Directory(PathObject, ABC):
    """
    A class that implements helper methods for working with directories (which are stored on a hard drive).
    :param path: The path to a directory
    """

    def __init__(self, path: Union[Path, str]):

        super().__init__(path)
        # parse directory to find contents and setup the directory structure.
        # THIS DOES NOT READ IN DIRECTORY CONTENTS
        self._parse()

    @abstractmethod
    def _parse(self) -> None:
        """
        Abstract method to find all relevant files within the directory.

        .. note::
            This is not reading the files just finding the paths to the files and setup the directory structure
        """
        pass

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """
        Implement if the path of the directory needs to be checked if it contains something specific
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
        return iter(natsorted(self.path.iterdir(), key=ignore_alpha))

    def __iter__(self):
        """When code iterates over an instance of a directory, it calls the pathlib iterdir() method which yields
        path objects to all directory contents."""
        return self.iterdir()

    @property
    def name(self):
        return self.path.name


class AnnotatedDirectory(Directory, ABC):
    """Abstract method for adding a parser for a Directory that
    has annotated files (such as GJF, Int, WFN). For example, look at the `PointDirectory` class.

    .. note::
        If multiple files with the same extensions are found, they will be stored in a list instead,
        so accessing an attribute might return a list if multiple files are found
        with the same extension
    """

    # must returns a dictionary, containing key: name of file (which is how one would access as attributes
    # using dot  notation in Python), and value: Python class (such as GJF, INT, WFN),
    contents = None

    # from https://stackoverflow.com/a/53769173
    def __init_subclass__(cls, **kwargs):
        if not getattr(cls, "contents"):
            raise TypeError(
                f"Can't instantiate abstract class {cls.__name__} without 'contents' class variable defined."
            )
        return super().__init_subclass__(**kwargs)

    @property
    def type_to_contents(self) -> dict:
        """Returns a dictionary containing the class as keys and the attributes as values.
        Reverses the self.contents attribute
        """
        return {v: k for k, v in self.contents}

    @property
    def _content_types(self) -> list:
        """Returns a list of the classes which are contained in the AnnotatedDirectory"""
        return list(self._contents.values())

    @cached_property
    def pathtypes(self) -> Dict[str, Type[PathObject]]:
        return {**self.filetypes, **self.dirtypes}

    @cached_property
    def filetypes(self) -> Dict[str, Type[File]]:
        """Returns a dictionary of key:value pairs where the keys are the attributes
        and the values are the type of class these attributes are going to
        be set to. These classes are all subclassing from the `File` class.
        For example {'gjf': GJF,  'wfn': WFN}."""
        filetypes = {}
        for f_name, f_class in self.contents:
            # GJF and WFN are subclasses of File for example
            if issubclass(f_class, File):
                filetypes[f_name] = f_class
        return filetypes

    @cached_property
    def dirtypes(self) -> Dict[str, Type[Directory]]:
        """Returns a dictionary of key:value pairs where the keys are
        the attributes and the values are the type of class these attributes are going to
        be set to. These classes are all subclassing from the `Directory` class.
        For example {'ints': INTs}."""
        dirtypes = {}
        for f_name, f_class in self.contents:
            # GJF and WFN are subclasses of File
            if issubclass(f_class, Directory):
                dirtypes[f_name] = f_class
        return dirtypes

    @property
    def files(self) -> List[File]:
        """Return all objects which are contained in the `AnnotatedDirectory`
        instance and that subclass from `File` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), File)
        ]

    @property
    def directories(self) -> List[Directory]:
        """Return all objects which are contained in the `AnnotatedDirectory`
        instance and that subclass from `Directory` class."""
        return [
            getattr(self, var)
            for var in vars(self)
            if isinstance(getattr(self, var), Directory)
        ]

    @property
    def path_objects(self) -> List[PathObject]:
        """Returns a list of PathObjects corresponding to files and directories
        that are in the instance of AnnotatedDirectory."""
        return self.files + self.directories

    def _parse(self):
        """
        Iterates over an `AnnotatedDirectory`'s contents (which are files or other sub-directories).
        If the content is a file, then check the filetype of the file (compared to the filetype
        which the classes subclassing from File have). After the check succeeds, check if that filetype
        needs a parent (meaning that the filetype needs access to the parent directory
        because it needs information from parent directory). For example, an .int file needs access to the parent
        directory because it needs the whole geometry ot calculate the ALF. The same is done for directories.
        """
        if not self.exists():
            return

        # set all to OptionalContent by default
        # in case a file/dir is being accessed, but it is not there
        for var, pathtype in self.pathtypes.items():
            setattr(self, var, OptionalContent)

        dir_contents = list(self.path.iterdir())

        # TODO: not sure how much this will slow down, as we are looping over contents
        # multiple times

        # iterate over the filetypes dictionary {"gjf": GJF, "wfn": WFN,......}
        for var, pathtype in self.pathtypes.items():
            # make a list of files/directories that match the same pattern
            list_with_same_extension = []
            # loop over contents of the directory and assign attributes depending on file suffixes
            for f in dir_contents:
                # if the suffix of the file matches the suffix of the class
                if pathtype.check_path(f):
                    # append file object to list
                    list_with_same_extension.append(pathtype(f))

            # if the list is not empty, then assign attribute
            # if list is empty, keep as OptionalContent
            if list_with_same_extension:
                # if only one element is found, then attribute is going to be an instance
                if len(list_with_same_extension) == 1:
                    setattr(self, var, list_with_same_extension[0])

                # if multiple elements in list, then attribute is going to be a list of instances
                else:
                    setattr(self, var, list_with_same_extension)

            # set to empty list for next class
            list_with_same_extension = []
