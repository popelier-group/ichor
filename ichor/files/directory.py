import re
from abc import ABC, abstractmethod

from ichor.common.functools import buildermethod, classproperty
from ichor.files.file import File, FileState
from ichor.files.path_object import PathObject


class Directory(PathObject, ABC):
    def __init__(self, path):
        super().__init__(path)
        self.parse()
        self.state = FileState.Unread

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

    @buildermethod
    def read(self) -> 'Directory':
        if self.state is FileState.Unread:
            self.state = FileState.Reading
            for var in vars(self):
                inst = getattr(self, var)
                if isinstance(inst, (File, Directory)):
                    inst.read()
            self.state = FileState.Read

    @classproperty
    @abstractmethod
    def dirpattern(self) -> re.Pattern:
        pass

    def iterdir(self):
        return iter(self)

    def __iter__(self):
        return self.path.iterdir()

    def __getattribute__(self, item):
        try:
            if (
                super().__getattribute__(item) is None
                and self.state is not FileState.Reading
            ):
                self.read()
        except AttributeError:
            self.read()
        return super().__getattribute__(item)
