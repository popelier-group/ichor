import re

from ichor.common.functools import buildermethod, classproperty
from ichor.common.sorting import natsort
from ichor.files.directory import Directory
from ichor.files.int import INT


class INTs(Directory, dict):
    def __init__(self, path):
        dict.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f)
        self.sort()

    def sort(self):
        # TODO: natural sort keys
        pass

    @classproperty
    def dirpattern(self):
        return re.compile(r".+_atomicfiles")

    @buildermethod
    def read(self):
        for atom, int_file in self.items():
            int_file.read()

    def __getattr__(self, item):
        if item not in self.__dict__.keys():
            try:
                return {
                    atom: getattr(int_, item) for atom, int_ in self.items()
                }
            except AttributeError:
                raise AttributeError(
                    f"'{self.__class__}' object has no attribute '{item}'"
                )
        return self.__dict__[item]
