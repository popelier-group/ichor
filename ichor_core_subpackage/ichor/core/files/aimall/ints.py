from pathlib import Path
from typing import Dict, List, Union

import numpy as np
from ichor.core.common.functools import classproperty
from ichor.core.common.sorting.natsort import ignore_alpha
from ichor.core.files.aimall.ab_int import ABINT
from ichor.core.files.aimall.int import INT
from ichor.core.files.directory import Directory
from ichor.core.files.file_data import HasProperties


class INTs(HasProperties, dict, Directory):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An Atoms instance that holds coordinate information for all the atoms in the system.
        Things like XYZ and GJF hold geometry.
    """

    def __init__(self, path: Union[Path, str]):
        Directory.__init__(self, path)
        dict.__init__(self)
        self.interaction_ints = {}

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
                self[f.stem.capitalize()] = INT(f)

            elif ABINT.check_path(f):
                a_atom, b_atom = f.stem.split()
                a = a_atom.capitalize()
                b = b_atom.capitalize()
                self.interaction_ints[(a, b)] = ABINT(f)

        self.sort()

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Checks if the given Path instance has _atomicfiles in its name."""
        return path.name.endswith("_atomicfiles")

    def sort(self):
        """Sorts keys of self by atom index e.g.
        {'H2': , 'H3': , 'O1': } -> {'O1': , 'H2': , 'H3': }"""
        dict.__init__(self, sorted(self.items(), key=lambda x: ignore_alpha(x[0])))

    @classproperty
    def property_names(self) -> List[str]:
        return INT.property_names

    def properties(self, C_dict: Dict[str, np.ndarray]) -> Dict[str, Dict[str, float]]:
        """
        Returns a dictionary of dictionaries containing atom names as keys an a dictionary
        as value. The value dictionary contains the properties we are interested in machine learning
        as keys and the values of these properties as floats. A list of C matrices needs to be
        passed in because we must rotate the multipoles.

        :param C_list: A list of rotation matrices, each of the atoms
        :raises FileNotFoundError: If no `C_matrix` is passed in and the wfn file associated
            with the int file does not exist. Then we cannot calculate multipoles.
        """

        return {
            atom_name: int_file_instance.properties(C_dict[int_file_instance.atom_name])
            for atom_name, int_file_instance in self.items()
        }

    def local_spherical_multipoles(
        self, C_dict: Dict[str, np.ndarray]
    ) -> Dict[str, Dict[str, float]]:

        """Rotates global spherical multipoles into local spherical multipoles. Optionally
        a rotation matrix can be passed in. Otherwise, the wfn file associated with this int file
        (as read in from the int file) will be used (if it exists).

        :param C_dict: A dictionary of rotation matrices, each of the atoms.
            This ensures that the correct C matrix is used for each atom.
        :raises FileNotFoundError: If no `C_matrix` is passed in and the wfn file associated
            with the int file does not exist. Then we cannot calculate multipoles.
        """

        return {
            atom_name: int_file_instance.local_spherical_multipoles(
                C_dict[int_file_instance.atom_name]
            )
            for atom_name, int_file_instance in self.items()
        }

    def __iter__(self):
        """Iterate over all INT instances (wrap around individual .int files)
        which are found in an INTs directory."""
        yield from self.values()

    def __str__(self):
        return f"INTs Directory: {self.path.absolute()}, containing .int for atoms names: {', '.join(self.keys())}"

    def __getattr__(self, item):
        return {
            atom_name: getattr(int_file_instance, item)
            for atom_name, int_file_instance in self.items()
        }
