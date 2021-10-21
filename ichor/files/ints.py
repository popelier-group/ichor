import re
from pathlib import Path
from typing import Optional

from ichor.common.functools import buildermethod, classproperty
from ichor.common.sorting.natsort import ignore_alpha, natsorted
from ichor.files.directory import Directory
from ichor.files.geometry import GeometryFile
from ichor.files.int import INT


class INTs(Directory, dict):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An `Atoms` instance that holds coordinate information for all the atoms in the system
    """

    def __init__(self, path, parent: Optional[GeometryFile] = None):
        self._parent = None
        if parent is not None:
            self.parent = parent
        dict.__init__(self)
        Directory.__init__(self, path)

    @property
    def parent(self) -> GeometryFile:
        if self._parent is None:
            raise ValueError(
                f"'parent' attribute for {self.path} instance of {self.__class__.__name__} is not defined"
            )
        return self._parent

    @parent.setter
    def parent(self, value: GeometryFile):
        if not isinstance(value, GeometryFile):
            raise TypeError(
                f"'parent' must be of type 'GeometryFile' not of type {type(value)}"
            )
        self._parent = value

    @buildermethod
    def read(self):
        """Read all the individual .int files. See the `INT` class for how one .int file is read."""
        for atom, int_file in self.items():
            int_file.read()

    def parse(self) -> None:
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f, self.parent)
        self.sort()

    def sort(self):
        """Sorts keys of self by atom index e.g.
        {'H2': , 'H3': , 'O1': } -> {'O1': , 'H2': , 'H3': }"""
        copy = self.copy()
        self.clear()
        for k in natsorted(list(copy.keys()), key=ignore_alpha):
            self[k] = copy[k]

    @classmethod
    def check_path(cls, path: Path) -> bool:
        return path.name.endswith("_atomicfiles")

    def revert_backup(self):
        """Moves original AIMALL files (which when parsed were converted to .int.bak) to .int files, deleting the json files which
        were written out as .int"""
        for atom, int_file in self.items():
            int_file.revert_backup()

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

    def __iter__(self):
        """ Iterate over all .int files which are found in an INTs directory."""

        for f in Directory.__iter__(self):
            if f.suffix == INT.filetype:
                yield f

    def iter_backup(self):
        """ Iterate over all .bak files which are found in an INTs directory"""

        for f in Directory.__iter__(self):
            if f.suffix == INT.backup_filetype:
                yield f
