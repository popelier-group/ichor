from abc import ABC, abstractmethod
from contextlib import contextmanager
from enum import Enum
from pathlib import Path
from typing import List, Optional, Union

from ichor.core.common.functools import buildermethod, classproperty
from ichor.core.common.io import move
from ichor.core.files.path_object import PathObject

class FileReadError(Exception):
    pass


class FileState(Enum):
    """An enum that is used to make it easier to check the current file state.
    Blocked is actually not used currently."""

    Unread = 1
    Reading = 2
    Read = 3
    Blocked = -1


class FileContentsType:
    """ A class whose instance is used for class attributes that are read in from a file.
    If a class attribute is FileContents type, then we read the file and store the read in value.
    This class allows for lazily reading files (i.e. files are not directly read in when
    an instance of a File (or its subclasses) is made, but only when attributes of that
    instance (which are FileContents) are being accessed."""
    pass

    def __bool__(self):
        """ FileContents instances must evaluate to False (as NoneType)."""
        return False

# make an instance of FileContentsType which to use everywhere.
FileContents = FileContentsType()

class File(PathObject, ABC):
    """Abstract Base Class for any type of file that is used by ICHOR."""

    state: FileState = FileState.Unread
    _contents: List[str] = []

    def __init__(self, path: Union[Path, str]):
        path = Path(path)
        # need to check if path exists here because if it does, we need to read in file contents
        if path.exists():
            super().__init__(path)
            self.state = FileState.Unread
            self._contents = []
        # if path does not exist, there is no file to read in from.
        # but can still construct file from passing in arguments / writing out default arguments
        else:
            super().__init__(path)
            self.state = FileState.Read            

    @property
    def title(self):
        """Returns the name of the WFN file (excluding the .wfn extension)"""
        return self.path.stem

    @buildermethod
    def read(self, *args, **kwargs):
        """Read the contents of the file. Depending on the type of file, different parts will be read in.
        
        .. note::
            Only files which exist on disk can be read from. Otherwise, nothing will be read in.
        """
        if not self.path.exists():
            raise ValueError("Cannot read file when self.path does not exist on disk.")

        if self.state is FileState.Unread:
            # TODO: remove this as some things might not be FileContents type as they can be set by user
            for var, inst in vars(self).items():
                if inst is FileContents:
                    self._contents.append(var)
            self.state = FileState.Reading
            self._read_file(
                *args, **kwargs
            )  # self._read_file is different based on which type of file is being read (GJF, AIMALL, etc.)
            self.state = FileState.Read
            # check all the contents are not FileContents at this point
            # TODO: add this check
            self.check_file_contents_exist()

    @abstractmethod
    def _read_file(self, *args, **kwargs):
        """ Abstract method detailing how to read contents of a file. Every type of file (gjf, int, etc.)
        is written in a different format and contains different information, so every file reading is
        different."""
        pass

    def check_file_contents_exist(self):
        pass

    @classproperty
    @abstractmethod
    def filetype(self) -> str:
        """ Abstract class property which returns the suffix associated with the filetype.
        For example, for GJF class, this will return `.gjf`"""
        pass

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """ Checks the suffix of the given path matches the filetype associated with class that subclasses from File
        :param path: A Path object to check
        :return: True if the Path object has the same suffix as the class filetype, False otherwise
        """
        return cls.filetype == path.suffix

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
        except AttributeError:
            pass

        try:
            return super().__getattribute__(item)
        except AttributeError:
            raise AttributeError(f"{self} does not have attribute {item}.")

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

    def move(self, dst):
        """Move the file to a new destination.

        :param dst: The new path to the file. If a directory, the file is moved inside the directory.
        """
        if dst.is_dir():
            # pathlib's Path class uses / operator to add to the path
            dst /= self.path.name
        move(self.path, dst)

    def dump(self):
        """ Sets all attributes in self._contents to FileContents. self._contents
        is a list of strings corresponding to attributes which are initially of type
        FileContents (and are changed when a file is read). This method essentially resets
        an instance to the time where the file associated with the instance is not read in yet
        and no data has been stored. Also resets the state to FileState.Unread ."""
        for var in self._contents:
            setattr(self, var, FileContents)
        self.state = FileState.Unread

    def write(self, path: Optional[Path] = None):
        """ This write method should only be called if no other write method exists. A
        write method is implemented for files that we typically write out (such as 
        .xyz or .gjf files). But other files (which are outputs of a program, such as .wfn,
        and .int), we only need to read and do not have to write out ourselves."""
        raise NotImplementedError(
            f"'write' method not implemented for {self.__class__.__name__}"
        )

    @contextmanager
    def block(self):
        """ Blocks a file from being read. Contents of the file cannot be read."""
        self._save_state = self.state
        try:
            self.state = FileState.Blocked
            yield
        finally:
            self.unblock()

    def unblock(self):
        """ Unblocks a blocked file."""
        if self.state is FileState.Blocked:
            self.state = self._save_state
    
    def __str__(self):
        if self.path.exists():
            return f"File Absolute Path: {self.path.absolute()}, Class Name: {self.__class__.__name__}"
        return f"File with path {self.path.absolute()} is not found on disk."