from abc import ABC, abstractmethod

from ichor.atoms import AtomsNotFoundError
from ichor.geometry import AtomData, Geometry, GeometryData


class Point(ABC, Geometry, GeometryData):
    @property
    def atoms(self):
        for var in vars(self):
            inst = getattr(self, var)
            if isinstance(inst, Geometry):
                return inst.atoms
        raise AtomsNotFoundError(f"Cannot find atoms for point {self}")

    @abstractmethod
    def get_atom_data(self, atom) -> AtomData:
        pass
        # return AtomData(self.atoms[atom], self.data[atom])

    def __getitem__(self, item):
        if isinstance(item, str):
            return self.get_atom_data(item)
        return super().__getitem__(item)
