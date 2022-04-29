from typing import Optional

from ichor.ichor_lib.atoms import Atom
from ichor.ichor_lib.common.types import ClassDict


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

    def __getattr__(self, item):
        try:
            return getattr(self.properties, item)
        except AttributeError:
            raise AttributeError(
                f"'{self.__class__}' object has no attribute '{item}'"
            )
