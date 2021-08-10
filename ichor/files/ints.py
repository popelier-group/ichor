import re

from ichor.common.functools import buildermethod, classproperty
from ichor.common.sorting import natsort
from ichor.files.directory import Directory
from ichor.files.int import INT


class INTs(Directory, dict):
    """Wraps around a directory which contains all .int files for the system."""
    def __init__(self, path):
        dict.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        """ Iterate over directory contents and find .int files. Add them to self, as self subclasses from dict."""
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f)
        self.sort()  # matt_todo: This is not implemented.

    def sort(self):
        # TODO: natural sort keys
        pass

    @classproperty
    def dirpattern(self) -> re.Pattern:
        """ Returns the regex pattern that needs to be in the directory name containing all .int files"""
        return re.compile(r".+_atomicfiles")

    @buildermethod
    def read(self):
        """Read all the individual .int files. See the `INT` class for how one .int file is read."""
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
