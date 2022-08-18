"""Tests if the atoms contains in the .xyz file are the same as reference Atoms."""

from ichor.core.atoms import Atom, Atoms
from ichor.core.files import XYZ
from tests.test_atoms import _test_atoms_coords
from tests.path import get_cwd
from ichor.core.common.units import AtomicDistance

example_dir = get_cwd(__file__) / "example_xyzs"


def test_water_dimer():
    xyz = XYZ(example_dir / "water-dimer.xyz")

    expected_atoms = Atoms(
        [
            Atom(
                "O",
                0.0000000000000000000,
                0.00000000000000000,
                0.00000000000000000,
            ),
            Atom(
                "H",
                -0.5350658173492745000,
                -0.96513545593593150,
                0.34177238995479650,
            ),
            Atom(
                "H",
                0.9912520884083418000,
                0.11847125457966462,
                -0.04195287155767175,
            ),
            Atom(
                "O",
                -6.243578624055563e-17,
                0.00000000000000000,
                -3.30362878833371450,
            ),
            Atom(
                "H",
                0.0000000000000000000,
                0.33294582772684770,
                -4.26739270395095400,
            ),
            Atom(
                "H",
                -6.180093092917877e-17,
                -0.93417428703609300,
                -3.63732168743662680,
            ),
        ]
    )

    _test_atoms_coords(xyz.atoms, expected_atoms, AtomicDistance.Angstroms)
