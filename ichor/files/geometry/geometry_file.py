from typing import Optional

from ichor.atoms import Atoms
from ichor.files.file import FileContents


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
