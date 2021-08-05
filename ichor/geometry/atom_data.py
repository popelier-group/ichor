from typing import Optional

from ichor.atoms import Atom
from ichor.common.types import ClassDict


class AtomData(Atom):
    properties: ClassDict

    def __init__(self, atom: Atom, properties: Optional[ClassDict] = None):
        Atom.__init__(
            self,
            atom.type,
            atom.x,
            atom.y,
            atom.z,
            index=atom.index,
            units=atom.units,
            parent=atom.parent,
        )
        self.properties = properties

    # def __getattr__(self, item):
    #     try:
    #         return getattr(self.properties, item)
    #     except AttributeError:
    #         raise AttributeError(f"Atom {self.name} has no attribute '{item}'")

    def __getattr__(self, item):
        try:
            super().__getattr__(item)
        except AttributeError:
            try:
                return getattr(self.properties, item)
            except AttributeError:
                raise AttributeError(
                    f"'{self.__class__}' object has no attribute '{item}'"
                )
        # try:
        #     for var, inst in self.__dict__.items():
        #         if isinstance(inst, (dict, ClassDict)) and item in inst.keys():
        #             a = inst[item]
        #             if isinstance(a, dict) and self.name in a.keys():
        #                 return a[self.name]
        #             return a
        #     raise AttributeError(
        #         f"'{self.__class__}' object has no attribute '{item}'"
        #     )
        # except KeyError:
        #     raise AttributeError(
        #         f"'{self.__class__}' object has no attribute '{item}'"
        #     )
