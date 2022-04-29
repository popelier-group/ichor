"""Handles a group of atoms (mostly used to group together atoms in the same chemical system).
 Each `Atoms` instance could contain multiple `Atom` instances."""

from ichor.ichor_lib.atoms.atom import Atom
from ichor.ichor_lib.atoms.atoms import Atoms
from ichor.ichor_lib.atoms.list_of_atoms import ListOfAtoms
from ichor.ichor_lib.atoms.atoms import AtomsNotFoundError, AtomNotFound
