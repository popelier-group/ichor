import json
from abc import ABC, abstractmethod
from typing import Any, Dict
from typing import List, Optional
import numpy as np

from ichor.core.common.dict import (
    find,
    unwrap_single_item,
    unwrap_item,
    remove_items,
)
from ichor.core.atoms import Atoms, Atom
from ichor.core.atoms.calculators import (
    FeatureCalculatorFunction,
    default_feature_calculator,
)
from ichor.core.files.file import FileContents, File
from pathlib import Path


class HasAtoms(ABC):
    """A class which is inherited from any file which contains the full geometry
    of the molecule/system. These geometries can be used to calculate connectivity
    and ALF. Files such as .xyz, .gjf, .wfn have the full geometry of the system
    (i.e. they have x,y,z coordinates for every atom in the system, but each file
    might have different units!). We can use any of these files to determine the
    connectivity or calculate the ALF.

    :param path: a path to a file
    """

    def __init__(self, atoms: Optional[Atoms] = None):
        self.atoms = FileContents if atoms is None else atoms

    @property
    def coordinates(self) -> np.ndarray:
        return self.atoms.coordinates

    @property
    def atom_names(self) -> List[str]:
        return [atom.name for atom in self.atoms]

    def features(
        self,
        feature_calculator: FeatureCalculatorFunction = default_feature_calculator,
    ) -> np.ndarray:
        return self.atoms.features(feature_calculator)

    def __getitem__(self, s: str):
        if isinstance(s, str) and s in self.atom_names:
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
    def properties(self) -> Dict[str, Any]:
        raise NotImplementedError(
            f"'data' not defined for '{self.__class__.__name__}'"
        )

    def get_property(self, _property: str) -> Any:
        return self.properties[_property]

    def __getattr__(self, item: str) -> Any:
        """Used to make values of GeometryData instances accessible as attributes.
        Looks into __dict__ of an instance to see if an instance of GeometryData exist.
        If an instance of GeometryData exists, it looks at the keys of that instance
        and the value is returned."""

        try:
            return unwrap_single_item(find(item, self.properties), item)
        except (KeyError, TypeError) as e:
            raise AttributeError(
                f"instance of '{self.__class__.__name__}' has no attribute '{item}'"
            ) from e


class AtomicData(Atom, HasProperties):
    def __init__(self, atom: Atom, properties: Dict[str, Any]):
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
        self._properties = self._select_properties(properties)

    @property
    def properties(self):
        return self._properties

    @properties.setter
    def properties(self, properties: Dict[str, Any]):
        self._properties = self._select_properties(properties)

    def _select_properties(self, _properties: Dict[str, Any]):
        return unwrap_item(
            remove_items(
                _properties, set(self._parent.atom_names) - {self.name}
            ),
            self.name,
        )


class Cacheable(ABC):
    def __init__(self, cache_path: Optional[Path] = None):
        self.cache_path: Path = cache_path or Path("cache")
        self._cache_attributes: bool = True
        self._cache_properties: bool = True

    @property
    def cacheable_objects(self) -> Dict[str, Any]:
        objects = {}
        if self._cache_attributes:
            for attr, value in var(self).items():
                objects[attr] = value

    def _serialize_cache(self):
        with open(self.cache_path, 'w') as f:
            json.dump(self.cacheable_objects, f)

    @abstractmethod
    def _deserialize_cache(self):
        raise NotImplementedError(f"'_deserialize_cache' not implemented for type '{self.__class__.__name__}'")
