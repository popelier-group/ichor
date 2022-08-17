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
    
def test_water_monomer_gau_file_without_forces():
    
    gau_file_path = example_dir / "water_monomer_no_forces.gau"
    
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
    
def test_water_monomer_gau_file_with_forces():
    
    gau_file_path = example_dir / "water_monomer_with_forces.gau"
    
    reference_forces = {"O1": AtomForce(0.029102177, 0.087242136, 0.000000000),
                        "H2": AtomForce(-0.026674154, -0.010235375, 0.000000000),
                        "H3": AtomForce(-0.002428023, -0.077006761,  0.000000000)}
    
    reference_atoms = Atoms([Atom("O", 0.00000000, 0.00000000,  0.00000000),
                             Atom("H", 0.99809000, 0.00000000, 0.00000000),
                             Atom("H", -0.09858000, 1.07846000, 0.00000000)])
    
    _test_read_gau(
        gau_path=gau_file_path,
        forces=reference_forces,
        charge=0,
        multiplicity=1,
        atoms=reference_atoms,
        molecular_dipole=MolecularDipole(x=1.3362, y=1.5253, z=0.0, total=2.0278),
        molecular_quadrupole=MolecularQuadrupole(xx=-5.3112, yy=-5.1244, zz=-7.9601, xy=-0.4487, xz=0.0, yz=0.0),
        traceless_molecular_quadrupole=TracelessMolecularQuadrupole(xx=0.8207, yy=1.0075, zz=-1.8282, xy=-0.4487, xz=0.0, yz=0.0),
        molecular_octapole=MolecularOctapole(xxx=0.3222, yyy=0.2308, zzz=0.0, xyy=-0.8355, xxy=-0.7487, xxz=0.0, xzz=-0.5908, yzz=-0.7743, yyz=0.0, xyz=0.0),
        molecular_hexadecapole=MolecularHexadecapole(xxxx=-6.9726, yyyy=-7.2644, zzzz=-8.0431, xxxy=-0.1772, xxxz=0.0, yyyx=-0.4713, yyyz=0.0, zzzx=0.0, zzzy=0.0, xxyy=-3.2206, xxzz=-2.9078, yyzz=-3.0768, xxyz=0.0, yyxz=0.0, zzxy=-0.0352)
    )
    
def test_glycine_gau_file_with_forces():
    
    gau_file_path = example_dir / "glycine_with_forces.log"
    
    reference_forces = {"C1": AtomForce(0.009062468, 0.001540764, -0.000442123),
                        "N2": AtomForce(0.002518463, -0.002186601, 0.000724210),
                        "H3": AtomForce(-0.003273520, 0.001261183, 0.003973730),
                        "C4": AtomForce(-0.007520073, 0.003573769, -0.003963447),
                        "H5": AtomForce(-0.004730779, -0.002583407, -0.002678228),
                        "C6": AtomForce(-0.007105918, 0.001819320, 0.000128651),
                        "O7": AtomForce(-0.012033306, -0.009026933, 0.006822045),
                        "N8": AtomForce(0.021877801, -0.006590017, 0.008465048),
                        "C9": AtomForce(-0.004340885, 0.000694133, -0.005218948),
                        "O10": AtomForce(0.000754285, 0.007797299, -0.005064322),
                        "C11": AtomForce(0.005784479, 0.002910005, -0.004232598),
                        "H12": AtomForce(-0.002663509, 0.006881399, -0.001456594),
                        "H13": AtomForce(-0.002090254, -0.004151253, -0.000714653),
                        "H14": AtomForce(0.002609111, 0.001589330, -0.002182237),
                        "H15": AtomForce(0.001017369, -0.001878448, 0.002165297),
                        "H16": AtomForce(-0.000258466, 0.001813343, 0.004116137),
                        "H17": AtomForce(0.000125501, -0.002745813, -0.002485166),
                        "H18": AtomForce(-0.005209573, -0.005096491, 0.002205491),
                        "H19": AtomForce(0.005476806, 0.004378417, -0.000162292),}
    
    reference_atoms = Atoms([Atom("C", -0.91371, 1.58371, 0.27699),
                            Atom("N", 0.52964, 1.47211, 0.27266),
                            Atom("H", -1.33731, 0.69538, -0.20217),
                            Atom("C", -1.34558, 2.83899, -0.47994),
                            Atom("H", -1.25812, 1.64233, 1.31428),
                            Atom("C", 1.1653, 0.41308, 0.86239),
                            Atom("O", -0.53703, 3.63634, -0.95225),
                            Atom("N", -2.71286, 2.99474, -0.56955),
                            Atom("C", -3.29203, 4.08859, -1.30755),
                            Atom("O", 0.56671, -0.50372, 1.41641),
                            Atom("C", 2.66687, 0.46335, 0.78788),
                            Atom("H", -3.27099, 3.84068, -2.37199),
                            Atom("H", -2.72496, 5.00744, -1.13614),
                            Atom("H", -4.32541, 4.22109, -0.97912),
                            Atom("H", 3.01445, 1.28987, 0.16199),
                            Atom("H", 3.03442, -0.47253, 0.35828),
                            Atom("H", 3.07026, 0.59161, 1.79577),
                            Atom("H", 1.04987, 2.23552, -0.15025),
                            Atom("H", -3.31391, 2.22812, -0.29334),])
    
    _test_read_gau(
        gau_path=gau_file_path,
        forces=reference_forces,
        charge=0,
        multiplicity=1,
        atoms=reference_atoms,
        molecular_dipole=MolecularDipole(x=-2.4751, y=1.687, z=-1.2018, total=3.2275),
        molecular_quadrupole=MolecularQuadrupole(xx=-36.2654, yy=-60.0278, zz=-58.3936, xy=-7.9603, xz=2.6513, yz=4.9482),
        traceless_molecular_quadrupole=TracelessMolecularQuadrupole(xx=15.2969, yy=-8.4655, zz=-6.8314, xy=-7.9603, xz=2.6513, yz=4.9482),
        molecular_octapole=MolecularOctapole(xxx=35.0823, yyy=-335.9408, zzz=-5.9367, xyy=-5.9503, xxy=-62.2619, xxz=-7.1871, xzz=21.8074, yzz=-102.7753, yyz=5.1616, xyz=10.8576),
        molecular_hexadecapole=MolecularHexadecapole(xxxx=-1148.5413, yyyy=-2112.6342, zzzz=-332.6197, xxxy=385.9354, xxxz=-176.9312, yyyx=400.3207, yyyz=239.1459, zzzx=-209.8154, zzzy=224.5097, xxyy=-424.9689, xxzz=-264.851, yyzz=-406.8596, xxyz=36.1749, yyxz=-36.8878, zzxy=167.0006)
    )