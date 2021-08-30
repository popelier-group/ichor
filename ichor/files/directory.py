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
        PathObject.__init__(self, path)  # set path for directory instance as well as FileState to Unread
        self.parse()  # parse directory to find contents
        self.parsed = True  # matt_todo: remove this attribute as it is not used anywhere else, the self.state is Unread from PathObject init

    # matt_todo: Possibly make this parse method an @abstractmethod with just pass inside
    # Then each class that subclasses from Directory will need its own parse method
    # This will prevent confusion with PointsDirectory calling Directory.__init__(self, path)
    # which then calls self.parse() in its init, but actually the PointsDirectory parse() method is still used
    # The current code that is in Directory parse() can then be moved into a parse() method in PointDirectory instead because
    # it is only used there.
    # Also then a self.parse() will need to be added to the __init__() methods of PointsDirectory and PointDirecory
    # but then you can easily tell which parse() method is being called
    def parse(self) -> None:
        """ matt_todo Move to PointDirectory parse and make this an abstract method.
        Iterate over __annotations__ which is a dictionary of {"gjf": Optional[GJF], "wfn": Optional[WFN], "ints": Optional[INTs]}
        as defined from class variables in PointsDirectory. Get the type inside the [] brackets
         """
        filetypes = {}
        dirtypes = {}
        for var, type_ in self.__annotations__.items():
            if hasattr(type_, "__args__"):
                type_ = type_.__args__[0]

            if issubclass(type_, File):
                filetypes[var] = type_
            elif issubclass(type_, Directory):
                dirtypes[var] = type_

        for f in self:  # calls the __iter__() method which yields pathlib Path objects for all files/folders inside a directory.
            if f.is_file():
                for var, filetype in filetypes.items():
                    if f.suffix == filetype.filetype:
                        if (
                            "parent"
                            in inspect.signature(filetype.__init__).parameters
                        ):
                            setattr(self, var, filetype(f, parent=self))
                        else:
                            setattr(self, var, filetype(f))
                        break
            elif f.is_dir():
                for var, dirtype in dirtypes.items():
                    if dirtype.dirpattern.match(f.name):
                        if (
                            "parent"
                            in inspect.signature(dirtype.__init__).parameters
                        ):
                            setattr(self, var, dirtype(f, parent=self))
                        else:
                            setattr(self, var, dirtype(f))
                        break

    def move(self, dst):
        # matt_todo: Does this actually move the files to the new location or just the Path object changes? What happens when you replace a path?
        """
        Move a directory object to a new location (a new path)
        :param dst: The new path of the directory
        """
        self.path.replace(dst)
        self.path = dst
        for f in self.path.iterdir():  # matt_todo: can just be for f in self because of how __iter__ is implemented.
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
        """ Read a directory and all of its contents and store information that ICHOR needs to function (such as .wfn or .int information that is needed.)
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
        # matt_todo: This is same as __iter__ method, so not sure if it is needed.
        return self.path.iterdir()

    def __iter__(self):
        """ When code iterates over an instance of a directory, it calls the pathlib iterdir() method which yields
        path objects to all directory contents."""
        return self.path.iterdir()
