from pathlib import Path
from typing import Optional, Union

from ichor.common.sorting.natsort import ignore_alpha, natsorted
from ichor.files.directory import Directory
from ichor.files.geometry import GeometryFile, AtomicDict
from ichor.files.int import INT


class INTs(Directory, AtomicDict):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An `Atoms` instance that holds coordinate information for all the atoms in the system
    """

    def __init__(
        self, path: Union[Path, str], parent: Optional[GeometryFile] = None
    ):
        self._parent = parent
        dict.__init__(self)
        Directory.__init__(self, path)

    def _parse(self) -> None:
        """ Parse an *_atomicfiles directory and look for .int files. This method is
        ran automatically when INTs is initialized. See Directory class which
        this class subclasses from.
        
        .. note::
            This method does NOT read in information from the INT files (i.e. multipoles 
            and iqa data are not read in here). This method only finds the relevant files.
            Once information is requested (i.e. multipoles or iqa are needed), the INT class
            _read_file method reads in the data.
        """
        for f in self:
            if f.suffix == INT.filetype:
                self[f.stem.upper()] = INT(f, self._parent)
        self.sort()

    @property
    def parent(self) -> GeometryFile:
        """ Returns a GeometryFile instance associated with the INTs. This is needed because the
        .int files are for individual atoms, but these atoms belong to a bigger molecule/system.
        The GeometryFile contains the information (coordinates) for the whole system."""
        if self._parent is None:
            raise ValueError(
                f"'parent' attribute for {self.path} instance of {self.__class__.__name__} is not defined"
            )
        return self._parent

    @parent.setter
    def parent(self, value: GeometryFile):
        """ Setter method for parent property."""
        if not isinstance(value, GeometryFile):
            raise TypeError(
                f"'parent' must be of type 'GeometryFile' not of type {type(value)}."
            )
        self._parent = value

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """ Checks if the given Path instance has _atomicfiles in its name."""
        return path.name.endswith("_atomicfiles")

    def dump(self):
        """ Removes the data from all the associated INT files, i.e. if the files
        were read in and iqa and multipole data was stored, this method will wipe that
        data and set all the attributes back to FileContents type.
        """
        for _, INT_instance in self.items():
            INT_instance.dump()

    def sort(self):
        """Sorts keys of self by atom index e.g.
        {'H2': , 'H3': , 'O1': } -> {'O1': , 'H2': , 'H3': }"""
        copy = self.copy()
        self.clear()
        for k in natsorted(list(copy.keys()), key=ignore_alpha):
            self[k] = copy[k]

    def __iter__(self):
        """Iterate over all INT instances (wrap around individual .int files)
        which are found in an INTs directory."""
        for INT_instance in self.values():
            yield INT_instance

