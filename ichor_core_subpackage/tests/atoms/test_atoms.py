from typing import Optional

import pytest
from ichor.core.atoms import Atoms


def _test_atoms_coords(atoms: Atoms, expected_atoms: Atoms):
    if expected_atoms is None:
        return

    assert len(atoms) == len(expected_atoms)
    for atom, expected_atom in zip(atoms, expected_atoms):
        assert atom.type == expected_atom.type
        assert atom.name == expected_atom.name
        assert atom.x == pytest.approx(expected_atom.x)
        assert atom.y == pytest.approx(expected_atom.y)
        assert atom.z == pytest.approx(expected_atom.z)


def _test_atoms_coords_optional(atoms: Atoms, expected_atoms: Optional[Atoms]):
    if expected_atoms is not None:
        _test_atoms_coords(atoms, expected_atoms)
