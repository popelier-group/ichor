import re
from abc import ABC, abstractmethod
from pathlib import Path

from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File, FileState
from ichor.files.path_object import PathObject


class Directory(PathObject, ABC):
    """A class that implements helper methods for working with directories (which are stored on a hard drive).
    :param path: The path to a directory"""
    def __init__(self, path):
        PathObject.__init__(self, path) # set path for directory instance as well as FileState to Unread
        self.parse() # parse directory to find contents
        self.parsed = True  # todo: remove this attribute as it is not used anywhere else, the self.state is Unread from PathObject init

    def parse(self) -> None:
        filetypes = {}
        dirtypes = {}
        for var, type_ in self.__annotations__.items():
            if hasattr(type_, "__args__"):
                type_ = type_.__args__[0]

            if issubclass(type_, File):
                filetypes[var] = type_
            elif issubclass(type_, Directory):
                dirtypes[var] = type_

        for f in self:
            if f.is_file():
                for var, filetype in filetypes.items():
                    if f.suffix == filetype.filetype:
                        setattr(self, var, filetype(f))
                        break
            elif f.is_dir():
                for var, dirtype in dirtypes.items():
                    if dirtype.dirpattern.match(f.name):
                        setattr(self, var, dirtype(f))
                        break

    def move(self, dst):
        """
        Move a directory to a new location (a new path)
        :param dst: The new path of the directory
        """

        self.path.replace(dst)  # todo: (from pathlib 3.8) This should be self.path = self.path.replace(dst) as .replace() returns a new Path instance pointing to dst 
        self.path = dst
        # todo: doesn't replacing the path automatically move all other files?
        for f in self.path.iterdir():
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
        # todo: Not sure what exactly it does
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
        return self.path.iterdir()

    def __iter__(self):
        return self.path.iterdir()
