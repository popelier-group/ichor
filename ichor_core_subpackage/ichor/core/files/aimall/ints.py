from pathlib import Path
from typing import Callable, Dict, Union

import numpy as np
from ichor.core.files.aimall.ab_int import AbInt
from ichor.core.files.aimall.int import Int
from ichor.core.files.directory import AnnotatedDirectory
from ichor.core.files.file_data import HasData


class IntDirectory(HasData, AnnotatedDirectory):
    """Wraps around a directory which contains all .int files for the system.

    :param path: The Path corresponding to a directory holding .int files
    :param parent: An Atoms instance that holds coordinate information for all the atoms in the system.
        Things like XYZ and GJF hold geometry.
    """

    contents = {"ints": Int, "interaction_ints": AbInt}

    def __init__(self, path: Union[Path, str]):

        AnnotatedDirectory.__init__(self, path)

    @property
    def raw_data(self) -> dict:
        """Returns data associated with each atom. If interaction ints are present,
        also adds these to the dictionary.
        """

        all_data = {i.atom_name: i.raw_data for i in self.ints}

        if self.interaction_ints:
            interactions_dict = {
                f"{i.a}_{i.b}": i.raw_data for i in self.interaction_ints
            }
            all_data.update(interactions_dict)

        return all_data

    def processed_data(self, processing_func: Callable) -> dict:
        """Processes all data and returns a dictionary of key: atom_name,
        value: processed data for that atom from multiple int files.

        At the moment, only A' data (encomp=3) can be processed.

        :param processing_func: callable to be passed to Int file instance
            which does the processing
        """

        return {i.atom_name: i.processed_data(processing_func) for i in self.ints}

    @classmethod
    def check_path(cls, path: Path) -> bool:
        """Checks if the given Path instance has _atomicfiles in its name."""
        return path.name.endswith("_atomicfiles")

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

    # TODO: remove, add to processing data
    # def local_spherical_multipoles(
    #     self, C_dict: Dict[str, np.ndarray]
    # ) -> Dict[str, Dict[str, float]]:

    #     """Rotates global spherical multipoles into local spherical multipoles. Optionally
    #     a rotation matrix can be passed in. Otherwise, the wfn file associated with this int file
    #     (as read in from the int file) will be used (if it exists).

    #     :param C_dict: A dictionary of rotation matrices, each of the atoms.
    #         This ensures that the correct C matrix is used for each atom.
    #     :raises FileNotFoundError: If no `C_matrix` is passed in and the wfn file associated
    #         with the int file does not exist. Then we cannot calculate multipoles.
    #     """

    #     return {
    #         atom_name: int_file_instance.local_spherical_multipoles(
    #             C_dict[int_file_instance.atom_name]
    #         )
    #         for atom_name, int_file_instance in self.items()
    #     }

    def __iter__(self):
        """Iterate over all INT instances (wrap around individual .int files)
        which are found in an INTs directory."""
        yield from self.values()

    def __str__(self):
        atm_names = [i.atom_name for i in self.ints]
        return f"INTs Directory: {self.path.absolute()}, containing .int for atoms names: {', '.join(atm_names)}"

    def __getattr__(self, item):
        return {
            atom_name: getattr(int_file_instance, item)
            for atom_name, int_file_instance in self.items()
        }

    def __getitem__(self, pattern: str):
        """Used to get particular int or interaction int by atom name or

        :param atom_name: _description_
        :type atom_name: str
        """
        pattern = pattern.capitalize()

        # look at int first
        if "_" not in pattern:
            return self.ints[pattern]

        # if pattern is not found here as well, it will raise KeyError
        return self.interaction_ints[pattern]
