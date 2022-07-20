from abc import ABC, abstractmethod
from typing import Any, Dict
from abc import ABC
from typing import List, Optional, Union, Callable
import numpy as np

from ichor.core.common.dict import (
    find,
    unwrap_single_item,
    unwrap_item,
    remove_items,
)
from ichor.core.atoms import Atom

class HasAtoms(ABC):
    """A class which is inherited from any file which contains the full geometry
    of the molecule/system. These geometries can be used to calculate connectivity
    and ALF. Files such as .xyz, .gjf, .wfn have the full geometry of the system
    (i.e. they have x,y,z coordinates for every atom in the system, but each file
    might have different units!). We can use any of these files to determine the
    connectivity or calculate the ALF.

    :param path: a path to a file
    """

    @property
    def coordinates(self) -> np.ndarray:
        return self.atoms.coordinates

    @property
    def atom_names(self) -> List[str]:
        return [atom.name for atom in self.atoms]

    def features(
        self,
        feature_calculator: Callable,
        *args,
        **kwargs
    ) -> np.ndarray:
        
        return self.atoms.features(feature_calculator, *args, **kwargs)

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

    # can be used to make sure either a method or property with name `properties` exists
    @abstractmethod
    def properties(self) -> Dict[str, Any]:
        raise NotImplementedError(
            f"'data' not defined for '{self.__class__.__name__}'"
        )

    def get_property(self, _property: str, *args, **kwargs) -> Any:
        return self.properties(*args, **kwargs)[_property]

class AtomicData(Atom, HasProperties):
    def __init__(self, atom: Atom, properties: Dict[str, Any] = None):
        Atom.__init__(
            self,
            atom.type,
            atom.x,
            atom.y,
            atom.z,
            atom.index,
            atom.parent,
            atom.units,
        )
        self._properties = properties

    @property
    def properties(self):
        return self._properties