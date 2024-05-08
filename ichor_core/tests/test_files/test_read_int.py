from pathlib import Path
from typing import Dict, List, Optional

import pytest
from ichor.core.common.types.itypes import T
from ichor.core.files import Int, XYZ
from ichor.core.files.aimall.int import CriticalPoint, CriticalPointType

from tests.path import get_cwd
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


def _assert_critical_point_instances(
    list_of_critical_points: T, expected_list_of_critical_points: Optional[T]
):

    """Asserts that a list of CriticalPoint instances is equal to a reference list of Critical Point Instances."""

    assert len(list_of_critical_points) == len(expected_list_of_critical_points)

    if expected_list_of_critical_points is not None:
        for cp, other_cp in zip(
            list_of_critical_points, expected_list_of_critical_points
        ):
            assert cp.index == other_cp.index
            assert cp.type == other_cp.type
            assert cp.x == pytest.approx(other_cp.x)
            assert cp.y == pytest.approx(other_cp.y)
            assert cp.z == pytest.approx(other_cp.z)
            assert cp.connecting_atoms == other_cp.connecting_atoms


def _test_int(
    int_file_path: Path,
    atom_name: str = None,
    atom_num: int = None,
    title: str = None,
    dft_model: str = None,
    basin_integration_results: Dict[str, float] = None,
    integration_error: float = None,
    critical_points: List[CriticalPoint] = None,
    bond_critical_points: List[CriticalPoint] = None,
    ring_critical_points: List[CriticalPoint] = None,
    cage_critical_points: List[CriticalPoint] = None,
    raw_data: Dict[str, float] = None,
    local_spherical_multipoles: Dict[str, float] = None,
    C_matrix=None,
    iqa_energy_components: Dict[str, float] = None,
    iqa: float = None,
    e_intra: float = None,
    q: float = None,
    q00: float = None,
    dipole_mag: float = None,
    total_time: int = None,
):
    """Tests original .int file from AIMALL is being read in correctly. No json
    file is generated anymore for .int files, so this is not tested."""

    int_file_instance = Int(int_file_path)

    _assert_val_optional(int_file_instance.atom_name, atom_name)
    _assert_val_optional(int_file_instance.atom_num, atom_num)
    _assert_val_optional(int_file_instance.title, title)

    _assert_val_optional(int_file_instance.dft_model, dft_model)
    _assert_val_optional(
        int_file_instance.basin_integration_results, basin_integration_results
    )
    _assert_val_optional(int_file_instance.integration_error, integration_error)

    _assert_critical_point_instances(int_file_instance.critical_points, critical_points)
    _assert_critical_point_instances(
        int_file_instance.bond_critical_points, bond_critical_points
    )
    _assert_critical_point_instances(
        int_file_instance.ring_critical_points, ring_critical_points
    )
    _assert_critical_point_instances(
        int_file_instance.cage_critical_points, cage_critical_points
    )

    _assert_val_optional(int_file_instance.iqa_energy_components, iqa_energy_components)
    _assert_val_optional(int_file_instance.iqa, iqa)
    _assert_val_optional(int_file_instance.e_intra, e_intra)
    _assert_val_optional(int_file_instance.q, q)
    _assert_val_optional(int_file_instance.q00, q00)

    # these require having a C matrix to rotate multipoles
    # TODO: If dipole magnitude stays the same since we are rotating only, technically can use original multipoles.
    if C_matrix is not None and local_spherical_multipoles is not None:
        _assert_val_optional(
            int_file_instance.local_spherical_multipoles(C_matrix),
            local_spherical_multipoles,
        )
        _assert_val_optional(int_file_instance.dipole_mag, dipole_mag)

    _assert_val_optional(int_file_instance.total_time, total_time)


def test_int_with_reference_geometry():

    from ichor.core.calculators.alf import calculate_alf_atom_sequence

    xyz_file_inst = XYZ(example_dir / "WATER_MONOMER0000.xyz")

    # calculate system alf and also calculate C matrix for atom of interest (O1)
    system_alf = xyz_file_inst.alf(calculate_alf_atom_sequence)
    o1_C_matrix = xyz_file_inst.C_matrix_dict(system_alf)["O1"]

    file_bond_critical_points = [
        CriticalPoint(
            index=1,
            ty=CriticalPointType("BCP"),
            x=-0.76721432416,
            y=0.1247579689,
            z=0.84654698766,
            connecting_atoms=["H2"],
        ),
        CriticalPoint(
            index=2,
            ty=CriticalPointType("BCP"),
            x=0.77030827811,
            y=0.19216479035,
            z=-0.82227408842,
            connecting_atoms=["H3"],
        ),
    ]

    reference_basin_integration_results = {
        "N": 9.051921199,
        "G": 74.791164088,
        "K": 74.791135363,
        "L": -2.8725236559e-05,
        "WeizKE": 56.710353062,
        "TFKE": 68.018165709,
        "I": 2.6259255233,
        "<Rho/r**2>": 255.26049285,
        "<Rho/r>": 22.898084753,
        "<Rho*r>": 9.4431536295,
        "<Rho*r**2>": 14.960646158,
        "<Rho*r**4>": 76.450299725,
        "GR(-2)": -254.74879402,
        "GR(-1)": -44.849872825,
        "GR0": -25.353568378,
        "GR1": -34.211989682,
        "GR2": -67.437532961,
        "VenO": -183.18467802,
        "VenT": -192.23207093,
        "Dipole X": 0.0018273275449,
        "Dipole Y": -0.20706556929,
        "Dipole Z": -0.020042356378,
        "|Dipole|": 0.20804130638,
    }
    reference_raw_data = {
        "iqa": -75.446714709,
        "integration_error": -2.8725236559e-05,
        "q00": -1.051921199,
        "q10": -0.020042356378,
        "q11c": 0.0018273275449,
        "q11s": -0.20706556929,
        "q20": -0.037266216811,
        "q21c": -0.79780613831,
        "q21s": 0.013146921148,
        "q22c": -0.19595266005,
        "q22s": 0.078488472227,
        "q30": 0.043015515207,
        "q31c": -0.053621704828,
        "q31s": 0.21644282193,
        "q32c": -0.029607236961,
        "q32s": -0.89197505111,
        "q33c": -0.053969314597,
        "q33s": 0.16211677693,
        "q40": -1.4545843935,
        "q41c": 0.91783517331,
        "q41s": 0.17650015949,
        "q42c": -0.73112185714,
        "q42s": -0.3293114897,
        "q43c": 2.8344280941,
        "q43s": -0.16267842746,
        "q44c": -1.3853362266,
        "q44s": 0.089771195512,
        "q50": -0.24411738335,
        "q51c": 0.48960856702,
        "q51s": -1.5472642317,
        "q52c": -0.040094542612,
        "q52s": 0.98097072569,
        "q53c": 0.72718022845,
        "q53s": -1.1988409017,
        "q54c": -0.47766441277,
        "q54s": 2.0753064137,
        "q55c": -0.29405113415,
        "q55s": -1.6430303594,
    }
    reference_local_spherical_multipoles = {
        "q00": -1.051921199,
        "q10": -5.971195811950436e-06,
        "q11c": -0.15123377206736352,
        "q11s": -0.14286193093736504,
        "q20": -0.7908309593839885,
        "q21c": -1.4464026698297726e-05,
        "q21s": -5.543942439588758e-06,
        "q22c": -0.020479344487304943,
        "q22s": -0.23828789712995924,
        "q30": -4.993875759830985e-06,
        "q31c": -0.3620726386379662,
        "q31s": -0.4187417600838701,
        "q32c": 1.1785015298312213e-05,
        "q32s": -5.586206568159201e-05,
        "q33c": 0.5782099716700353,
        "q33s": -0.48630823722629324,
        "q40": 1.5287789522503465,
        "q41c": 0.000751342068247478,
        "q41s": -0.00030596675807390537,
        "q42c": -0.11371535390793461,
        "q42s": 0.11619148494967288,
        "q43c": 0.0010842786899901149,
        "q43s": 0.0007843678785888553,
        "q44c": 3.306733465622479,
        "q44s": 0.5674077254927813,
    }
    reference_iqa_energy_components = {
        "T(A)": 74.791135363,
        "Vneen(A,A)/2 = Vne(A,A)": -183.18467802,
        "Vne(A,Mol)/2": -93.188839608,
        "Ven(A,Mol)/2": -96.116035467,
        "Vneen(A,Mol)/2": -189.30487508,
        "Vne(A,A')/2": -1.5965005983,
        "Ven(A,A')/2": -4.5236964569,
        "Vneen(A,A')/2": -6.1201970552,
        "Vee0(A,A) + Vee0(A,A')/2": 35.380176417,
        "Vee(A,A) + Vee(A,A')/2": 34.991706668,
        "VeeC(A,A) + VeeC(A,A')/2": 43.897749107,
        "VeeX0(A,A) + VeeX0(A,A')/2": -8.5175726902,
        "VeeX(A,A) + VeeX(A,A')/2": -8.9060424385,
        "Vnn(A,Mol)/2": 4.0753183353,
        "Vee0(A,A)": 33.798035377,
        "Vee(A,A)": 33.409565629,
        "VeeC(A,A)": 42.110506649,
        "VeeX0(A,A)": -8.3124712718,
        "VeeX(A,A)": -8.7009410201,
        "Vee0(A,A')/2": 1.5821410393,
        "Vee(A,A')/2": 1.5821410393,
        "VeeC(A,A')/2": 1.7872424577,
        "VeeX0(A,A')/2": -0.20510141843,
        "VeeX(A,A')/2": -0.20510141843,
        "V_IQA(A)": -150.23785007,
        "VC_IQA(A)": -141.33180763,
        "VX_IQA(A)": -8.9060424385,
        "V_IQA(A,A)": -149.77511239,
        "VC_IQA(A,A)": -141.07417137,
        "VX_IQA(A,A)": -8.7009410201,
        "V_IQA(A,A')/2": -0.46273768055,
        "VC_IQA(A,A')/2": -0.25763626212,
        "VX_IQA(A,A')/2": -0.20510141843,
        "E_IQA0(A)": -75.05824496,
        "E_IQA(A)": -75.446714709,
        "E_IQA_Intra0(A)": -74.59550728,
        "E_IQA_Intra(A)": -74.983977028,
        "E_IQA_Inter0(A)": -0.46273768055,
        "E_IQA_Inter(A)": -0.46273768055,
    }

    _test_int(
        # since only o1 int, only need rotation matrix for O1 atom, but we can pass in dictionary for whole molecule
        # as the code is written to be able to rotate single atoms using a list of ALFs
        # (as long as the alf for the specific atom is in the list)
        int_file_path=example_dir / "WATER_MONOMER0000_atomicfiles" / "o1.int",
        atom_name="O1",
        atom_num=1,
        title="WATER_MONOMER0000",
        dft_model="Restricted B3LYP",
        basin_integration_results=reference_basin_integration_results,
        integration_error=-2.8725236559e-05,
        # there are only bond critical points in water monomer
        critical_points=file_bond_critical_points,
        bond_critical_points=file_bond_critical_points,
        ring_critical_points=[],
        cage_critical_points=[],
        raw_data=reference_raw_data,
        local_spherical_multipoles=pytest.approx(
            reference_local_spherical_multipoles,
            abs=1e-6,
        ),
        C_matrix=o1_C_matrix,
        iqa_energy_components=reference_iqa_energy_components,
        iqa=-75.446714709,
        e_intra=-74.983977028,
        q=-1.051921199,
        q00=-1.051921199,
        dipole_mag=pytest.approx(0.2080413063805621),
        total_time=33,
    )
