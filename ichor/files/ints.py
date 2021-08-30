import re

from ichor.common.functools import buildermethod, classproperty
from ichor.common.sorting import natsort
from ichor.files.directory import Directory
from ichor.files.int import INT


class INTs(Directory, dict):
    # matt_todo: check if parent parameter is correctly described
    """Wraps around a directory which contains all .int files for the system.
    
    :param path: The Path corresponding to a directory holding .int files
    :param parent: An `Atoms` instance that holds coordinate information for all the atoms in the system
    """
    def __init__(self, path, parent=None):
        self.parent = parent
        dict.__init__(self)
        Directory.__init__(self, path)

    def parse(self) -> None:
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f, self.parent)
        self.sort() # matt_todo: This is not implemented.

    def sort(self):
        # matt_todo: This is where natural sort is used, but is not implemented yet.
        # TODO: natural sort keys
        pass

    @classproperty
    def dirpattern(self):
        """ Returns the regex pattern that needs to be in the directory name containing all .int files"""
        return re.compile(r".+_atomicfiles")

    @buildermethod
    def read(self):
        """Read all the individual .int files. See the `INT` class for how one .int file is read."""
        for atom, int_file in self.items():
            # int_file.parent = self.atoms
            int_file.read()

    def __getattr__(self, item):
        # matt_todo: Is this so that you can access all attributes of `INT` instances from this `INTs` class?
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
