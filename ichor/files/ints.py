import re

from ichor.common.functools import buildermethod, classproperty
from ichor.common.sorting.natsort import natsorted, ignore_alpha
from ichor.files.directory import Directory
from ichor.files.int import INT


class INTs(Directory, dict):
    # todo: check if parent parameter is correctly described
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
        self.sort()

    def sort(self):
        """ Sorts keys of self by atom index e.g.
        {'H2': , 'H3': , 'O1': } -> {'O1': , 'H2': , 'H3': }"""
        copy = self.copy()
        self.clear()
        for k in natsorted(list(copy.keys()), key=ignore_alpha):
            self[k] = copy[k]

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
        """
        If an attribute is requested that is not in INTs but is an attribute of INT, a dictionary
        of the attributes are returned. e.g.

        ```python
        >>> ints.iqa
        {'O1': 76.51, 'H2': 0.52, 'H3': 0.53}
        ```
        """
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
