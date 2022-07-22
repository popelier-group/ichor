from abc import ABC, abstractmethod
from typing import Any, Dict
from abc import ABC
from typing import List, Callable
import numpy as np
from ichor.core.calculators.alf import ALF

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
        return {atom_instance.name: atom_instance.alf(alf_calculator) for atom_instance in self.atoms}

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

    def __getitem__(self, s: str):
        if isinstance(s, str):
            return self.atoms[s]
        # raises error message
        return super().__getitem__(s)

class HasProperties(ABC):
    """
    Class used to describe a file containing properties/data for a particular geometry

    Adds the method `get_property` which can be used to search for a property of a geometry
    Adds the ability to search for a property using dictionaries in the inherited class
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
    """ Wraps around a PointDirectory Dictionary to be able to index it in a certain way"""
    
    def __init__(self, data: dict):
        
        super().__init__(data)
        
    def __getitem__(self, key: str) -> dict:
        
        if key in self.keys():
            return super().__getitem__(key)
        
        # if key is not found, it should throw a KeyError
        return unwrap_single_entry(find_in_inner_dicts(key, self))
    
class PointsDirectoryProperties(dict):
    """ Wraps around a PointDirectory Dictionary to be able to index it in a certain way"""
    
    def __init__(self, data: dict):
        
        super().__init__(data)
        
    def __getitem__(self, key: str) -> dict:
        
        res = {}
        for point_dir_name, point_dir_properties in self.items():

            if key in point_dir_properties.keys():
                res[point_dir_name] = point_dir_properties[key]
            
            else:
                res[point_dir_name] = unwrap_single_entry(find_in_inner_dicts(key, point_dir_properties))
            
        return res