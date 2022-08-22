from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, Union
from pathlib import Path
from abc import ABC
from typing import List, Callable
import numpy as np
from ichor.core.atoms.alf import ALF

from ichor.core.common.dict import (
    find_in_inner_dicts,
    unwrap_single_item,
    unwrap_single_entry
)
from ichor.core.atoms import Atom

class HasAtoms(ABC):
    """
    Abstract base class for classes which either have a property or attribute of `atoms` that gives back an `Atoms` instance.
    """

    @property
    def coordinates(self) -> np.ndarray:
        return self.atoms.coordinates

    @property
    def atom_names(self) -> List[str]:
        return [atom.name for atom in self.atoms]
    
    @property
    def natoms(self) -> int:
        return len(self.atom_names)
    
    @property
    def types_extended(self) -> List[str]:
        return self.atoms.types_extended

    def connectivity(self, connectivity_calculator: Callable[..., np.ndarray]) -> np.ndarray:
        """Return the connectivity matrix (n_atoms x n_atoms) for the given Atoms instance.

        Returns:
            :type: `np.ndarray` of shape n_atoms x n_atoms
        """

        return connectivity_calculator(self.atoms)
    
    def C_matrix_dict(self, system_alf: List[ALF]) -> Dict[str, np.ndarray]:
        """ Returns a dictionary of key (atom name), value (C matrix np array) for every atom"""
        return {atom_instance.name: atom_instance.C(system_alf) for atom_instance in self.atoms}
    
    def C_matrix_list(self, system_alf: List[ALF]) -> List[np.ndarray]:
        """ Returns a list C matrix np array for every atom"""
        return [atom_instance.C(system_alf) for atom_instance in self.atoms]

    def alf(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[ALF]:
        """Returns the Atomic Local Frame (ALF) for all Atom instances that are held in Atoms
        e.g. [[0,1,2],[1,0,2], [2,0,1]]
        """
        return [alf_calculator(atom_instance, *args, **kwargs) for atom_instance in self.atoms]

    def alf_list(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[List[int]]:
        """ Returns a list of lists with the atomic local frame indices for every atom (0-indexed)."""
        return [[alf.origin_idx, alf.x_axis_idx, alf.xy_plane_idx] for alf in self.atoms.alf(alf_calculator, *args, **kwargs)]

    def alf_dict(self, alf_calculator: Callable[..., ALF], *args, **kwargs) -> List[List[int]]:
        """ Returns a list of lists with the atomic local frame indices for every atom (0-indexed)."""
        return {atom_instance.name: atom_instance.alf(alf_calculator, *args, **kwargs) for atom_instance in self.atoms}

    def features(
        self,
        feature_calculator: Callable,
        *args,
        **kwargs
    ) -> np.ndarray:
        
        return self.atoms.features(feature_calculator, *args, **kwargs)
    
    def features_dict(self, feature_calculator: Callable[..., np.ndarray], *args, **kwargs) -> dict:
        """Returns the features in a dictionary for this Atoms instance, corresponding to the features of each Atom instance held in this Atoms isinstance
        Features are calculated in the Atom class and concatenated to a 2d array here.

        e.g. {"C1": np.array, "H2": np.array}
        """

        return {atom_instance.name: atom_instance.features(feature_calculator, *args, **kwargs) for atom_instance in self.atoms}

    def center_geometry_on_atom_and_write_xyz(
        self,
        central_atom_alf: ALF,
        central_atom_name: str,
        fname: Optional[Union[str, Path]] = None,
        **kwargs
    ):
        """Centers all geometries (from a Trajectory of PointsDirectory instance) onto a central atom and then writes out a new
        xyz file with all geometries centered on that atom. This is essentially what the ALFVisualizier application (ALFi) does.
        The features for the central atom are calculated, after which they are converted back into xyz coordinates (thus all geometries)
        are now centered on the given central atom).

        :param feature_calculator: Function which calculates features
        :param central_atom_name: the name of the central atom to center all geometries on. Eg. `O1`
        :param fname: Optional file name in which to save the rotated geometries.
        :param *args: Positional arguments to pass to calculator function
        :param **kwargs: Key word arguments to pass to calculator function
        """

        from ichor.core.atoms import Atoms
        from ichor.core.files import XYZ
        from ichor.core.useful_functions import alf_features_to_coordinates
        from ichor.core.calculators import calculate_alf_features
        from ichor.core.common.units import AtomicDistance

        if central_atom_name not in self.atom_names:
            raise ValueError(
                f"Central atom name {central_atom_name} not found in atom names:{self.atom_names}."
            )

        if not fname:
            fname = f"{central_atom_name}_centered_geometries.xyz"
            fname = Path(fname)
        else:
            fname = Path(fname)
            fname = fname.with_suffix(".xyz")

        # before, ordering is 0,1,2,3,4,5,...,etc.
        # after calculating the features and converting back, the order is going to be
        # central atom idx, x-axis atom index, xy-plane atom index, rest of atom indices
        n_atoms = len(self.atom_names)
        
        previous_atom_ordering = list(range(n_atoms))
        current_atom_ordering = list(central_atom_alf) + [
            i for i in range(n_atoms) if i not in central_atom_alf
        ]
        # this will get the index that the atom was moved to after reordering.
        reverse_alf_ordering = [
            current_atom_ordering.index(num) for num in range(n_atoms)
        ]
        # order will always be central atom(0,0,0), x-axis atom, xy-plane atom, etc.
        
        central_atom_features = self.atoms[central_atom_name].features(calculate_alf_features, central_atom_alf)
        xyz_array = alf_features_to_coordinates(central_atom_features)

        # reverse the ordering, so that the rows are the same as before
        # can now use the atom names as they were read in in initial Trajectory/PointsDirectory instance.
        xyz_array[:, previous_atom_ordering, :] = xyz_array[
            :, reverse_alf_ordering, :
        ]
        
        # there is only one geometry here
        xyz_array = xyz_array[0]
        trajectory = XYZ(fname)
        
        # initialize empty Atoms instance
        atoms = Atoms()
        for ty, atom_coord in zip(self.types_extended, xyz_array):
            # add Atom instances for every atom in the geometry to the Atoms instance
            atoms.add(
                Atom(
                    ty,
                    atom_coord[0],
                    atom_coord[1],
                    atom_coord[2],
                    units=AtomicDistance.Bohr,
                )
            )
        # Add the filled Atoms instance to the Trajectory instance and repeat for next geometry
        atoms = atoms.to_angstroms()
        trajectory.atoms = atoms

        trajectory.write()

    def __getitem__(self, s: str):
        if isinstance(s, str):
            return self.atoms[s]
        # raises error message
        return super().__getitem__(s)

class HasProperties(ABC):
    """
    Class used to describe a file containing properties/data for a particular geometry
    """

    @property
    @abstractmethod
    def property_names(self) -> List[str]:
        """ Returns a list of strings corresponding to property names that the object should have"""
        ...

    # can be used to make sure either a method or property with name `properties` exists
    @abstractmethod
    def properties(self) -> Dict[str, Any]:
        ...

class PointDirectoryProperties(dict):
    """ Wraps around a PointDirectory dictionary containing properties (things we plan to machine learn)
        to be able to index it in a certain way"""
    
    def __init__(self, data: dict):
        
        super().__init__(data)
        
    def __getitem__(self, key: str) -> dict:
        
        # if in keys, we can directly return it
        if key in self.keys():
            return super().__getitem__(key)
        
        # if not in keys, then recursively search.
        # cannot use find function because that results in recursion (as find calls this __getitem__)
        return unwrap_single_entry(find_in_inner_dicts(key, self))
    
class PointsDirectoryProperties(dict):
    """ Wraps around a PointsDirectory dictionary containing properties (things we plan to machine learn)
        to be able to index it in a certain way"""
    
    def __init__(self, data: dict):
        
        super().__init__(data)
        
    def __getitem__(self, key: str) -> dict:
        
        # if in keys, we can directly return it
        # this will be used if key is a directory name in PointsDirectory
        if key in self.keys():
            return super().__getitem__(key)
        
        res = {}
        for point_dir_name, point_dir_properties in self.items():

            if key in point_dir_properties.keys():
                res[point_dir_name] = point_dir_properties[key]
            
            else:
                res[point_dir_name] = unwrap_single_entry(find_in_inner_dicts(key, point_dir_properties))
            
        return res