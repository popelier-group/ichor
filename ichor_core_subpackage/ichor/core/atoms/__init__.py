"""Handles a group of atoms (mostly used to group together atoms in the same chemical system).
 Each `Atoms` instance could contain multiple `Atom` instances."""

from ichor.core.atoms.atom import Atom, ConnectedAtom
from ichor.core.atoms.atoms import AtomNotFound, Atoms, AtomsNotFoundError, ConnectedAtoms
from ichor.core.atoms.list_of_atoms import ListOfAtoms
from ichor.core.atoms.alf import ALF
from ichor.core.atoms.list_of_atoms_atom_view import AtomView

