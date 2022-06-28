from collections import OrderedDict
from pathlib import Path
from typing import Dict, Union

from ichor.core.atoms import Atoms
from ichor.core.common.sorting.natsort import ignore_alpha, natsorted
from ichor.core.files.directory import Directory
from ichor.core.files.file_data import HasProperties

# from ichor.core.files.geometry import AtomicDict, AtomicData
from ichor.core.files.int import INT, ParentNotDefined


class INTs(HasProperties, OrderedDict, Directory):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An Atoms instance that holds coordinate information for all the atoms in the system.
        Things like XYZ and GJF hold geometry.
    """

    def __init__(
        self,
        path: Union[Path, str],
        parent: Atoms = None
    ):
        Directory.__init__(self, path)
        OrderedDict.__init__(self)
        self.parent = parent

    def _parse(self) -> None:
        """Parse an *_atomicfiles directory and look for .int files. This method is
        ran automatically when INTs is initialized. See Directory class which
        this class subclasses from.

        .. note::
            This method does NOT read in information from the INT files (i.e. multipoles
            and iqa data are not read in here). This method only finds the relevant files.
            Once information is requested (i.e. multipoles or iqa are needed), the INT class
            _read_file method reads in the data.
        """
        for f in self.iterdir():
            if f.suffix == INT.filetype:
                self[f.stem.capitalize()] = INT(f, parent=self.parent)
        self.sort()

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Checks if the given Path instance has _atomicfiles in its name."""
        return path.name.endswith("_atomicfiles")

    def sort(self):
        """Sorts keys of self by atom index e.g.
        {'H2': , 'H3': , 'O1': } -> {'O1': , 'H2': , 'H3': }"""
        OrderedDict.__init__(
            self, sorted(self.items(), key=lambda x: ignore_alpha(x[0]))
        )

    @property
    def properties(self) -> Dict[str, Dict[str, float]]:
        return {
            atom_name: int_file_instance.properties
            for atom_name, int_file_instance in self.items()
        }

    def __iter__(self):
        """Iterate over all INT instances (wrap around individual .int files)
        which are found in an INTs directory."""
        yield from self.values()

    def __str__(self):
        return f"INTs Directory: {self.path.absolute()}, containing .int for atoms names: {', '.join(self.keys())}"
