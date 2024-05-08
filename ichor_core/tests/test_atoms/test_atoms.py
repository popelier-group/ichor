from typing import Optional

import pytest
from ichor.core.atoms import Atoms
from ichor.core.common.units import AtomicDistance


def _test_atoms_coords(atoms: Atoms, expected_atoms: Atoms, units: AtomicDistance):

    """Asserts that an instance of Atoms is equal to a reference Atoms instance. Atomic Units are also needed
    to check that files containing Atoms instances have the correct units defined."""

    if expected_atoms is None:
        return

    assert len(atoms) == len(expected_atoms)
    for atom, expected_atom in zip(atoms, expected_atoms):
        assert atom.type == expected_atom.type
        assert atom.name == expected_atom.name
        assert atom.x == pytest.approx(expected_atom.x)
        assert atom.y == pytest.approx(expected_atom.y)
        assert atom.z == pytest.approx(expected_atom.z)
        # assume the same units for all atoms
        assert atom.units == units


def _test_atoms_coords_optional(
    atoms: Atoms, expected_atoms: Optional[Atoms], units: AtomicDistance
):
    if expected_atoms is not None:
        _test_atoms_coords(atoms, expected_atoms)
