"""Tests if the atoms contains in the .xyz file are the same as reference Atoms."""

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.units import AtomicDistance
from ichor.core.files import XYZ

from tests.path import get_cwd
from tests.test_atoms import _test_atoms_coords


example_dir = (
    get_cwd(__file__)
    / ".."
    / ".."
    / ".."
    / "example_files"
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
    / "WATER_MONOMER0000.pointdir"
)


def test_water_dimer():
    xyz = XYZ(example_dir / "WATER_MONOMER0000.xyz")

    expected_atoms = Atoms(
        [
            Atom("O", -0.03348733, -0.46689766, -0.00424905),
            Atom(
                "H",
                -0.50428226,
                0.20263196,
                0.56694849,
            ),
            Atom(
                "H",
                0.53776959,
                0.26426570,
                -0.56269944,
            ),
        ]
    )

    _test_atoms_coords(xyz.atoms, expected_atoms, AtomicDistance.Angstroms)
