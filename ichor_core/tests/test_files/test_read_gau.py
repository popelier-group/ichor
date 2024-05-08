from pathlib import Path
from typing import Dict

import numpy as np

from ichor.core.atoms import Atom, Atoms
from ichor.core.common.types.multipole_moments import (
    MolecularDipole,
    MolecularHexadecapole,
    MolecularOctupole,
    MolecularQuadrupole,
    TracelessMolecularQuadrupole,
)
from ichor.core.common.units import AtomicDistance

from ichor.core.files import GaussianOutput

from tests.path import get_cwd
from tests.test_atoms import _test_atoms_coords
from tests.test_files import _assert_val_optional

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


def _assert_atomic_forces(
    gau_file_forces: Dict[str, np.ndarray], reference_file_forces: Dict[str, np.ndarray]
):

    """Asserts that dictionary of Gaussian calcualted forces is equal to another dictionary of reference forces."""

    # forces might not be present in the gau file because forces
    # are only calculated when using "force" keyword in .gjf file
    if gau_file_forces and reference_file_forces:
        for reference_atom_name, reference_atom_forces in reference_file_forces.items():
            np.testing.assert_allclose(
                gau_file_forces[reference_atom_name], reference_atom_forces
            )


def _test_read_gau(
    gau_path: Path,
    forces: Dict[str, np.ndarray] = None,
    charge: int = None,
    multiplicity: int = None,
    atoms: Atoms = None,
    molecular_dipole: MolecularDipole = None,
    molecular_quadrupole: MolecularQuadrupole = None,
    traceless_molecular_quadrupole: TracelessMolecularQuadrupole = None,
    molecular_octupole: MolecularOctupole = None,
    molecular_hexadecapole: MolecularHexadecapole = None,
):
    """Test function for .gau/.log Gaussian output file."""

    gau_file = GaussianOutput(gau_path)

    _assert_atomic_forces(gau_file.global_forces, forces)
    _assert_val_optional(gau_file.charge, charge)
    _assert_val_optional(gau_file.multiplicity, multiplicity)
    _test_atoms_coords(gau_file.atoms, atoms, AtomicDistance.Angstroms)
    _assert_val_optional(gau_file.molecular_dipole, molecular_dipole)
    _assert_val_optional(gau_file.molecular_quadrupole, molecular_quadrupole)
    _assert_val_optional(
        gau_file.traceless_molecular_quadrupole, traceless_molecular_quadrupole
    )
    _assert_val_optional(gau_file.molecular_octupole, molecular_octupole)
    _assert_val_optional(gau_file.molecular_hexadecapole, molecular_hexadecapole)


def test_water_monomer_gau_file_with_forces():

    gau_file_path = example_dir / "WATER_MONOMER0000.gaussianoutput"

    reference_forces = {
        "O1": np.array([0.029533145, 0.082720401, -0.024953052]),
        "H2": np.array([0.005789613, -0.024283097, -0.008424334]),
        "H3": np.array([-0.035322758, -0.058437305, 0.033377387]),
    }

    reference_atoms = Atoms(
        [
            Atom("O", -0.033487, -0.466898, -0.004249),
            Atom("H", -0.504282, 0.202632, 0.566948),
            Atom("H", 0.537770, 0.264266, -0.562699),
        ]
    )

    _test_read_gau(
        gau_path=gau_file_path,
        forces=reference_forces,
        charge=0,
        multiplicity=1,
        atoms=reference_atoms,
        molecular_dipole=MolecularDipole(x=0.1189, y=2.3866, z=0.0787),
        molecular_quadrupole=MolecularQuadrupole(
            xx=-6.5273, yy=-7.7674, zz=-6.2577, xy=0.0665, xz=-1.6318, yz=-0.0495
        ),
        traceless_molecular_quadrupole=TracelessMolecularQuadrupole(
            xx=0.3235, yy=-0.9166, zz=0.5931, xy=0.0665, xz=-1.6318, yz=-0.0495
        ),
        molecular_octupole=MolecularOctupole(
            xxx=0.5348,
            yyy=8.5805,
            zzz=0.2229,
            xyy=0.1794,
            xxy=3.0830,
            xxz=0.0727,
            xzz=0.1817,
            yzz=3.0764,
            yyz=0.0143,
            xyz=0.0059,
        ),
        molecular_hexadecapole=MolecularHexadecapole(
            xxxx=-8.2830,
            yyyy=-15.2596,
            zzzz=-8.1733,
            xxxy=-0.2961,
            xxxz=-0.1375,
            yyyx=-0.2960,
            yyyz=0.0560,
            zzzx=-0.1975,
            zzzy=0.0334,
            xxyy=-3.8880,
            xxzz=-2.4818,
            yyzz=-3.8474,
            xxyz=-0.0404,
            yyxz=-0.2009,
            zzxy=-0.0859,
        ),
    )
