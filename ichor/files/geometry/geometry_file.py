from typing import Optional

from ichor.atoms import Atoms
from ichor.files.file import FileContents
from ichor.files.geometry.atom_data import AtomData

class GeometryFile:
    atoms: Optional[Atoms]

    def __init__(self):
        self.atoms = FileContents

    @property
    def features(self):
        return self.atoms.features

    @property
    def atom_names(self):
        return [atom.name for atom in self.atoms]

    def __getitem__(self, item):
        """ Returns all the data associated with an atom name"""
        if isinstance(item, str) and item in self.atoms.names:
            return AtomData(self.atoms[item], properties=self)
        return super().__getitem__(item)
