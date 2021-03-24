from abc import ABC
from ichor.atoms import AtomsNotFoundError
from ichor.geometry import Geometry


class Point(Geometry, ABC):
    @property
    def atoms(self):
        for var in vars(self):
            inst = getattr(self, var)
            if isinstance(inst, Geometry):
                return inst.atoms
        raise AtomsNotFoundError(f"Cannot find atoms for point {self}")
