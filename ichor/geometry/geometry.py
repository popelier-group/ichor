from typing import Optional

from ichor.atoms import Atoms


class Geometry:
    atoms: Optional[Atoms]

    def __init__(self):
        self.atoms = None

    @property
    def features(self):
        return self.atoms.features

    @property
    def atom_names(self):
        return [atom.name for atom in self.atoms]

    def __getitem__(self, item):
        return self.atoms[item]

    def __len__(self):
        return len(self.atoms)
