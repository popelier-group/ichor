"""Handles a group of atoms (mostly used to group together atoms in the same chemical system).
 Each `Atoms` instance could contain multiple `Atom` instances."""

from ichor.atoms.atom import Atom
from ichor.atoms.atoms import Atoms
from ichor.atoms.list_of_atoms import ListOfAtoms

__all__ = [
    "Atom",
    "Atoms",
    "ListOfAtoms",
    "AtomsNotFoundError",
]


class AtomsNotFoundError(Exception):
    pass
