"""Handles a group of atoms (mostly used to group together atoms in the same chemical system).
 Each `Atoms` instance could contain multiple `Atom` instances."""

from ichor_lib.atoms.atom import Atom
from ichor_lib.atoms.atoms import Atoms
from ichor_lib.atoms.list_of_atoms import ListOfAtoms

__all__ = [
    "Atom",
    "Atoms",
    "ListOfAtoms",
    "AtomsNotFoundError",
]


class AtomsNotFoundError(Exception):
    pass
