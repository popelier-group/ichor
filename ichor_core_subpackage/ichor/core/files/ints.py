from collections import OrderedDict
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
from ichor.core.atoms import Atoms
from ichor.core.common.sorting.natsort import ignore_alpha
from ichor.core.files.directory import Directory
from ichor.core.files.file_data import HasProperties

# from ichor.core.files.geometry import AtomicDict, AtomicData
from ichor.core.files.int import INT, ABInt


class INTs(HasProperties, OrderedDict, Directory):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An Atoms instance that holds coordinate information for all the atoms in the system.
        Things like XYZ and GJF hold geometry.
    """

    def __init__(self, path: Union[Path, str], parent: Atoms = None):
        # parent above __init__s because Directory.__init__ calls self._parse
        self.parent = parent
        Directory.__init__(self, path)
        OrderedDict.__init__(self)
        self.interaction_ints = OrderedDict()

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
            if INT.check_path(f):
                self[f.stem.capitalize()] = INT(f, parent=self.parent)
            elif ABInt.check_path(f):
                a, b = f.stem.split()
                a = a.capitalize()
                b = b.capitalize()
                self.interaction_ints[(a, b)] = ABInt(f)

        for (a, b), i in self.interaction_ints.values():
            self[a].interactions[b] = i
            self[b].interactions[a] = i

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

    def local_spherical_multipoles(
        self, C_matrix: Optional[List[np.ndarray]] = None
    ) -> Dict[str, Dict[str, float]]:
        """Rotates global spherical multipoles into local spherical multipoles. Optionally
        a rotation matrix can be passed in. Otherwise, the wfn file associated with this int file
        (as read in from the int file) will be used (if it exists).

        :param C_matrix: Optional rotation matrix to be used to rotate multipoles.
        :raises FileNotFoundError: If no `C_matrix` is passed in and the wfn file associated
            with the int file does not exist. Then we cannot calculate multipoles.
        """

        # if C_matrix is None, then the self.parent will be used by default in INT class
        # to calculate the C matrix
        return {
            atom_name: int_file_instance.local_spherical_multipoles(
                C_matrix[int_file_instance.i]
            )
            for atom_name, int_file_instance in self.items()
        }

    def __iter__(self):
        """Iterate over all INT instances (wrap around individual .int files)
        which are found in an INTs directory."""
        yield from self.values()

    def __str__(self):
        return f"INTs Directory: {self.path.absolute()}, containing .int for atoms names: {', '.join(self.keys())}"
