from pathlib import Path
from typing import Dict

from ichor.core.files import GaussianOut
from ichor.core.atoms import Atoms, Atom
from ichor.core.files.gaussian.gaussian_out import AtomForce, MolecularDipole, TracelessMolecularQuadrupole, MolecularQuadrupole, MolecularOctapole, MolecularHexadecapole
from ichor.core.common.types.itypes import T
from tests.path import get_cwd
from tests.test_files import _assert_val_optional
from tests.test_atoms import _test_atoms_coords
from ichor.core.common.units import AtomicDistance

import pytest

example_dir = get_cwd(__file__) / "example_gaus"

def _assert_atomic_forces(gau_file_forces: Dict[str, AtomForce], reference_file_forces: Dict[str, AtomForce]):
    
    # forces might not be present in the gau file because forces are only calculated when using "force" keyword in .gjf file
    if gau_file_forces and reference_file_forces:
        for reference_atom_name, reference_atom_forces in reference_file_forces.items():
            assert gau_file_forces[reference_atom_name].x == pytest.approx(reference_atom_forces.x)
            assert gau_file_forces[reference_atom_name].y == pytest.approx(reference_atom_forces.y)
            assert gau_file_forces[reference_atom_name].z == pytest.approx(reference_atom_forces.z)


def _test_read_gau(
    gau_path: Path,
    forces: Dict[str, AtomForce] = None,
    charge: int = None,
    multiplicity: int = None,
    atoms: Atoms = None,
    molecular_dipole: MolecularDipole = None,
    molecular_quadrupole: MolecularQuadrupole = None,
    traceless_molecular_quadrupole: TracelessMolecularQuadrupole = None,
    molecular_octapole: MolecularOctapole = None,
    molecular_hexadecapole: MolecularHexadecapole = None,
):
    
    gau_file = GaussianOut(gau_path)
    
    _assert_atomic_forces(gau_file.forces, forces)
    _assert_val_optional(gau_file.charge, charge)
    _assert_val_optional(gau_file.multiplicity, multiplicity)
    _test_atoms_coords(gau_file.atoms, atoms, AtomicDistance.Angstroms)
    _assert_val_optional(gau_file.molecular_dipole, molecular_dipole)
    _assert_val_optional(gau_file.molecular_quadrupole, molecular_quadrupole)
    _assert_val_optional(gau_file.traceless_molecular_quadrupole, traceless_molecular_quadrupole)
    _assert_val_optional(gau_file.molecular_octapole, molecular_octapole)
    _assert_val_optional(gau_file.molecular_hexadecapole, molecular_hexadecapole)
    
def test_gau_file_without_forces():
    
    gau_file_path = example_dir / "WATER_MONOMER0001.gau"
    
    reference_forces = {}
    
    reference_atoms = Atoms([Atom("O", -0.03349, -0.4669, -0.00425),
                             Atom("H", -0.50428, 0.20263, 0.56695 ),
                             Atom("H", 0.53777, 0.26427, -0.5627)])
    
    _test_read_gau(
        gau_path=gau_file_path,
        forces=reference_forces,
        charge=0,
        multiplicity=1,
        atoms=reference_atoms,
        molecular_dipole=MolecularDipole(x=0.1426, y=2.3942, z=0.0535, total=2.3991),
        molecular_quadrupole=MolecularQuadrupole(xx=-6.4806, yy=-7.7366, zz=-6.204, xy=0.0721, xz=-1.6772, yz=-0.0534),
        traceless_molecular_quadrupole=TracelessMolecularQuadrupole(xx=0.3265, yy=-0.9296, zz=0.6031, xy=0.0721, xz=-1.6772, yz=-0.0534),
        molecular_octapole=MolecularOctapole(xxx=0.5715, yyy=8.4307, zzz=0.1809, xyy=0.1988, xxy=3.0691, xxz=0.0434, xzz=0.1882, yzz=3.0845, yyz=0.0037, xyz=-0.1253),
        molecular_hexadecapole=MolecularHexadecapole(xxxx=-8.4442, yyyy=-15.1828, zzzz=-8.3154, xxxy=-0.284, xxxz=-0.1887, yyyx=-0.2953, yyyz=0.0517, zzzx=-0.264, zzzy=0.0379, xxyy=-3.8874, xxzz=-2.4725, yyzz=-3.8541, xxyz=-0.0366, yyxz=-0.1597, zzxy=-0.0788)
    )