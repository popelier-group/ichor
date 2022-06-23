from abc import ABC, abstractmethod
from typing import Any, Dict

from ichor.core.files import File, FileState

import typing
from collections.abc import MutableMapping


from abc import ABC
from pathlib import Path
from typing import List, Optional

import numpy as np

from ichor.core.common.dict import find, unwrap_single_item
from ichor.core.atoms import Atoms
from ichor.core.atoms.calculators import (
    FeatureCalculatorFunction,
    default_feature_calculator,
)
from ichor.core.files.file import FileContents


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


class DataFile(File, ABC):
    """
    Class used to describe a file containing properties/data for a particular geometry

    Adds the method `get_property` which can be used to search for a property of a geometry
    Adds the ability to search for a property using dictionaries in the inherited class
    """

    @property
    @abstractmethod
    def properties(self) -> Dict[str, Any]:
        raise NotImplementedError(
            f"'properties' not defined for '{self.__class__.__name__}'"
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
        except KeyError as e:
            raise AttributeError(
                f"'{self.path}' instance of '{self.__class__.__name__}' has no attribute '{item}'"
            ) from e
