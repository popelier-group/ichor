from abc import ABC
from typing import Any

from ichor.files.geometry.atom_data import AtomData
from ichor.files.geometry.geometry_file import GeometryFile


class PropertyNotFound(Exception):
    pass


class GeometryData(ABC):
    """
    Class used to describe a file containing properties of a geometry

    Adds the method `get_property` which can be used to search for a property of a geometry
    Adds the ability to search for a property using dictionaries in the inherited class
    """

    def get_property(self, item: str) -> Any:
        try:
            return getattr(self, item)
        except AttributeError:
            raise PropertyNotFound(f"Property {item} not found")

    def __getattr__(self, item: str) -> Any:
        for var, inst in self.__dict__.items():
            if isinstance(inst, dict) and item in inst.keys():
                return inst[item]
        raise AttributeError(
            f"'{self.__class__}' object has no attribute '{item}'"
        )

    def __getitem__(self, item):
        if isinstance(item, str):
            if isinstance(self, GeometryFile):
                return AtomData(self.atoms[item], properties=self)
        return super().__getitem__(item)
