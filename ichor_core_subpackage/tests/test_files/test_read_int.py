from pathlib import Path
from typing import List, Optional, Dict
from contextlib import suppress
from ichor.core.files import INT, XYZ
from ichor.core.files.int import CriticalPoint
from ichor.core.itypes import T
from tests.path import get_cwd
from ichor.core.atoms import Atoms
from ichor.core.files.int import (
    CriticalPoint,
    CriticalPointType,
    ParentNotDefined,
)
import pytest

example_dir = get_cwd(__file__) / "example_ints"


def _assert_val_optional(value: T, expected_value: Optional[T]):
    if expected_value is not None:
        assert value == expected_value


def _assert_critical_point_instances(
    list_of_critical_points: T, expected_list_of_critical_points: Optional[T]
):

    assert len(list_of_critical_points) == len(
        expected_list_of_critical_points
    )

    if expected_list_of_critical_points is not None:
        for cp, other_cp in zip(
            list_of_critical_points, expected_list_of_critical_points
        ):
            assert cp.index == other_cp.index
            assert cp.type == other_cp.type
            assert cp.x == other_cp.x
            assert cp.y == other_cp.y
            assert cp.z == other_cp.z
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
    properties: Dict[str, float] = None,
    net_charge: float = None,
    global_spherical_multipoles: Dict[str, float] = None,
    local_spherical_multipoles: Dict[str, float] = None,
    C_matrix = None,
    iqa_energy_components: Dict[str, float] = None,
    iqa: float = None,
    e_intra: float = None,
    q: float = None,
    q00: float = None,
    dipole_mag: float = None,
    total_time: int = None
):
    """Tests original .int file from AIMALL is being read in correctly. No json
    file is generated. json is checked in another test."""

    int_file_instance = INT(int_file_path)

    _assert_val_optional(int_file_instance.atom_name, atom_name)
    _assert_val_optional(int_file_instance.atom_num, atom_num)
    _assert_val_optional(int_file_instance.title, title)

    _assert_val_optional(int_file_instance.dft_model, dft_model)
    _assert_val_optional(
        int_file_instance.basin_integration_results, basin_integration_results
    )
    _assert_val_optional(
        int_file_instance.integration_error, integration_error
    )

    _assert_critical_point_instances(
        int_file_instance.critical_points, critical_points
    )
    _assert_critical_point_instances(
        int_file_instance.bond_critical_points, bond_critical_points
    )
    _assert_critical_point_instances(
        int_file_instance.ring_critical_points, ring_critical_points
    )
    _assert_critical_point_instances(
        int_file_instance.cage_critical_points, cage_critical_points
    )

    _assert_val_optional(int_file_instance.net_charge, net_charge)
    _assert_val_optional(
        int_file_instance.global_spherical_multipoles,
        global_spherical_multipoles,
    )

    _assert_val_optional(
        int_file_instance.iqa_energy_components, iqa_energy_components
    )
    _assert_val_optional(int_file_instance.iqa, iqa)
    _assert_val_optional(int_file_instance.e_intra, e_intra)
    _assert_val_optional(int_file_instance.q, q)
    _assert_val_optional(int_file_instance.q00, q00)

    # these require having the parent attribute because we need the C matrix to rotate multipoles
    # TODO: If dipole magnitude stays the same since we are rotating only (does it?), technically can use original multipoles.
    if C_matrix and local_spherical_multipoles:
        _assert_val_optional(
            int_file_instance.local_spherical_multipoles(C_matrix),
            local_spherical_multipoles,
        )
        _assert_val_optional(int_file_instance.dipole_mag, dipole_mag)
        _assert_val_optional(int_file_instance.properties, properties)

    _assert_val_optional(int_file_instance.total_time, total_time)

def test_no_parent_int():

    file_bond_critical_points = [
        CriticalPoint(
            index=1,
            ty=CriticalPointType("BCP"),
            x=-7.6381542088e-01,
            y=1.1484931659e-01,
            z=8.4198108911e-01,
            connecting_atoms=["H2"],
        ),
        CriticalPoint(
            index=2,
            ty=CriticalPointType("BCP"),
            x=7.5472805821e-01,
            y=1.6630947183e-01,
            z=-8.0755694711e-01,
            connecting_atoms=["H3"],
        ),
    ]

    _test_int(
        int_file_path=example_dir / "o1.int",
        atom_name="O1",
        atom_num=1,
        title="WATER_MONOMER0001",
        dft_model="Restricted B3LYP",
        basin_integration_results={
            "N": 9.0762060817,
            "G": 75.038982117,
            "K": 75.03894204,
            "L": -4.0077877571e-05,
            "WeizKE": 56.664620514,
            "TFKE": 68.244617363,
            "I": 2.6389848033,
            "<Rho/r**2>": 256.01273421,
            "<Rho/r>": 22.954908618,
            "<Rho*r>": 9.4998961933,
            "<Rho*r**2>": 15.172894906,
            "<Rho*r**4>": 80.51045651,
            "GR(-2)": -255.50489747,
            "GR(-1)": -44.988821679,
            "GR0": -25.507286293,
            "GR1": -34.656605556,
            "GR2": -69.046214277,
            "VenO": -183.63926895,
            "VenT": -192.68868344,
            "Dipole X": -0.0016461566576,
            "Dipole Y": -0.25708969568,
            "Dipole Z": -0.020646892538,
            "|Dipole|": 0.25792269313,
        },
        integration_error=-4.0077877571e-05,
        # there are only bond critical points in water monomer
        critical_points=file_bond_critical_points,
        bond_critical_points=file_bond_critical_points,
        ring_critical_points=[],
        cage_critical_points=[],
        properties=None,
        net_charge=-1.0762060817,
        global_spherical_multipoles={
            "q00": -1.0762060817,
            "q10": -0.020646892538,
            "q11c": -0.0016461566576,
            "q11s": -0.25708969568,
            "q20": -0.021700469782,
            "q21c": -0.75018382635,
            "q21s": 0.017792037022,
            "q22c": -0.16232546581,
            "q22s": 0.065122302165,
            "q30": 0.044683217585,
            "q31c": -0.089287472207,
            "q31s": 0.30596239543,
            "q32c": -0.063395331291,
            "q32s": -1.391653952,
            "q33c": -0.067954891804,
            "q33s": 0.20594440588,
            "q40": -1.9609913177,
            "q41c": 1.1488477959,
            "q41s": 0.26702238434,
            "q42c": -0.75531442849,
            "q42s": -0.39080307859,
            "q43c": 3.6310817472,
            "q43s": -0.24247145429,
            "q44c": -1.7369385615,
            "q44s": 0.072615449798,
            "q50": -0.41836505357,
            "q51c": 0.53462091556,
            "q51s": -2.2325774531,
            "q52c": -0.13994550028,
            "q52s": 1.5489383968,
            "q53c": 0.84062227501,
            "q53s": -1.567560763,
            "q54c": -0.41193097157,
            "q54s": 3.1313064283,
            "q55c": -0.31126569086,
            "q55s": -2.3600710711,
        },
        local_spherical_multipoles=None,
        C_matrix=None,
        iqa_energy_components={
            "T(A)": 75.03894204,
            "Vneen(A,A)/2 = Vne(A,A)": -183.63926895,
            "Vne(A,Mol)/2": -93.400150506,
            "Ven(A,Mol)/2": -96.344341721,
            "Vneen(A,Mol)/2": -189.74449223,
            "Vne(A,A')/2": -1.5805160326,
            "Ven(A,A')/2": -4.5247072473,
            "Vneen(A,A')/2": -6.1052232799,
            "Vee0(A,A) + Vee0(A,A')/2": 35.538139035,
            "Vee(A,A) + Vee(A,A')/2": 35.145962157,
            "VeeC(A,A) + VeeC(A,A')/2": 44.071057668,
            "VeeX0(A,A) + VeeX0(A,A')/2": -8.5329186324,
            "VeeX(A,A) + VeeX(A,A')/2": -8.9250955109,
            "Vnn(A,Mol)/2": 4.0753183136,
            "Vee0(A,A)": 33.972313611,
            "Vee(A,A)": 33.580136733,
            "VeeC(A,A)": 42.300500739,
            "VeeX0(A,A)": -8.3281871282,
            "VeeX(A,A)": -8.7203640066,
            "Vee0(A,A')/2": 1.5658254241,
            "Vee(A,A')/2": 1.5658254241,
            "VeeC(A,A')/2": 1.7705569283,
            "VeeX0(A,A')/2": -0.20473150425,
            "VeeX(A,A')/2": -0.20473150425,
            "V_IQA(A)": -150.52321176,
            "VC_IQA(A)": -141.59811625,
            "VX_IQA(A)": -8.9250955109,
            "V_IQA(A,A)": -150.05913221,
            "VC_IQA(A,A)": -141.33876821,
            "VX_IQA(A,A)": -8.7203640066,
            "V_IQA(A,A')/2": -0.46407954221,
            "VC_IQA(A,A')/2": -0.25934803796,
            "VX_IQA(A,A')/2": -0.20473150425,
            "E_IQA0(A)": -75.092092839,
            "E_IQA(A)": -75.484269717,
            "E_IQA_Intra0(A)": -74.628013297,
            "E_IQA_Intra(A)": -75.020190175,
            "E_IQA_Inter0(A)": -0.46407954221,
            "E_IQA_Inter(A)": -0.46407954221,
        },
        iqa=-7.5484269717e01,
        e_intra=-75.020190175,
        q=-1.0762060817,
        q00=-1.0762060817,
        dipole_mag=0.2579226931234475,
        total_time=184,
    )


def test_int_with_parent():
    
    from ichor.core.calculators.alf import calculate_alf_cahn_ingold_prelog

    xyz_file_inst = XYZ(
        example_dir / "example_parent_water_monomer_geometry.xyz"
    )
    
    # calculate system alf and also calculate C matrices for all atoms
    system_alf = xyz_file_inst.alf(calculate_alf_cahn_ingold_prelog)
    C_matrices_dict = xyz_file_inst.C_matrix_dict(system_alf)

    file_bond_critical_points = [
        CriticalPoint(
            index=1,
            ty=CriticalPointType("BCP"),
            x=-7.6381542088e-01,
            y=1.1484931659e-01,
            z=8.4198108911e-01,
            connecting_atoms=["H2"],
        ),
        CriticalPoint(
            index=2,
            ty=CriticalPointType("BCP"),
            x=7.5472805821e-01,
            y=1.6630947183e-01,
            z=-8.0755694711e-01,
            connecting_atoms=["H3"],
        ),
    ]

    _test_int(
        # since only o1 int, only need rotation matrix for O1 atom, but we can pass in dictionary for whole molecule
        # as the code is written to be able to rotate single atoms using a list of ALFs (as long as the alf for the specific atom is in the list)
        int_file_path=example_dir / "o1.int",
        atom_name="O1",
        atom_num=1,
        title="WATER_MONOMER0001",
        dft_model="Restricted B3LYP",
        basin_integration_results={
            "N": 9.0762060817,
            "G": 75.038982117,
            "K": 75.03894204,
            "L": -4.0077877571e-05,
            "WeizKE": 56.664620514,
            "TFKE": 68.244617363,
            "I": 2.6389848033,
            "<Rho/r**2>": 256.01273421,
            "<Rho/r>": 22.954908618,
            "<Rho*r>": 9.4998961933,
            "<Rho*r**2>": 15.172894906,
            "<Rho*r**4>": 80.51045651,
            "GR(-2)": -255.50489747,
            "GR(-1)": -44.988821679,
            "GR0": -25.507286293,
            "GR1": -34.656605556,
            "GR2": -69.046214277,
            "VenO": -183.63926895,
            "VenT": -192.68868344,
            "Dipole X": -0.0016461566576,
            "Dipole Y": -0.25708969568,
            "Dipole Z": -0.020646892538,
            "|Dipole|": 0.25792269313,
        },
        integration_error=-4.0077877571e-05,
        # there are only bond critical points in water monomer
        critical_points=file_bond_critical_points,
        bond_critical_points=file_bond_critical_points,
        ring_critical_points=[],
        cage_critical_points=[],
        properties=pytest.approx(
            {
                "iqa": -7.5484269717e01,
                "q00": -1.0762060817,
                "q10": 1.0691792094197914e-05,
                "q11c": -0.18349802926630163,
                "q11s": -0.18125283106512072,
                "q20": -0.7306931079095452,
                "q21c": 4.6244408763014356e-05,
                "q21s": 6.704034223640453e-05,
                "q22c": -0.007251302241812528,
                "q22s": -0.24533386519866374,
                "q30": -0.00015693945082017637,
                "q31c": -0.6029723942764993,
                "q31s": -0.6667364080049145,
                "q32c": -3.202830951170124e-05,
                "q32s": 0.00022118289876187804,
                "q33c": 0.8817616713685893,
                "q33s": -0.7111368504957145,
                "q40": 2.1290443376815316,
                "q41c": -0.00021690919606803517,
                "q41s": -3.053702959917118e-05,
                "q42c": -0.08077252837422033,
                "q42s": 0.23264809822968793,
                "q43c": 0.000524356914281114,
                "q43s": 0.0005797695619292943,
                "q44c": 4.139038945420569,
                "q44s": 0.7074733504033711,
            },
            abs=1e-6,
        ),
        net_charge=-1.0762060817,
        global_spherical_multipoles={
            "q00": -1.0762060817,
            "q10": -0.020646892538,
            "q11c": -0.0016461566576,
            "q11s": -0.25708969568,
            "q20": -0.021700469782,
            "q21c": -0.75018382635,
            "q21s": 0.017792037022,
            "q22c": -0.16232546581,
            "q22s": 0.065122302165,
            "q30": 0.044683217585,
            "q31c": -0.089287472207,
            "q31s": 0.30596239543,
            "q32c": -0.063395331291,
            "q32s": -1.391653952,
            "q33c": -0.067954891804,
            "q33s": 0.20594440588,
            "q40": -1.9609913177,
            "q41c": 1.1488477959,
            "q41s": 0.26702238434,
            "q42c": -0.75531442849,
            "q42s": -0.39080307859,
            "q43c": 3.6310817472,
            "q43s": -0.24247145429,
            "q44c": -1.7369385615,
            "q44s": 0.072615449798,
            "q50": -0.41836505357,
            "q51c": 0.53462091556,
            "q51s": -2.2325774531,
            "q52c": -0.13994550028,
            "q52s": 1.5489383968,
            "q53c": 0.84062227501,
            "q53s": -1.567560763,
            "q54c": -0.41193097157,
            "q54s": 3.1313064283,
            "q55c": -0.31126569086,
            "q55s": -2.3600710711,
        },
        local_spherical_multipoles=pytest.approx(
            {
                "q00": -1.0762060817,
                "q10": 1.0691792094197914e-05,
                "q11c": -0.18349802926630163,
                "q11s": -0.18125283106512072,
                "q20": -0.7306931079095452,
                "q21c": 4.6244408763014356e-05,
                "q21s": 6.704034223640453e-05,
                "q22c": -0.007251302241812528,
                "q22s": -0.24533386519866374,
                "q30": -0.00015693945082017637,
                "q31c": -0.6029723942764993,
                "q31s": -0.6667364080049145,
                "q32c": -3.202830951170124e-05,
                "q32s": 0.00022118289876187804,
                "q33c": 0.8817616713685893,
                "q33s": -0.7111368504957145,
                "q40": 2.1290443376815316,
                "q41c": -0.00021690919606803517,
                "q41s": -3.053702959917118e-05,
                "q42c": -0.08077252837422033,
                "q42s": 0.23264809822968793,
                "q43c": 0.000524356914281114,
                "q43s": 0.0005797695619292943,
                "q44c": 4.139038945420569,
                "q44s": 0.7074733504033711,
            },
            abs=1e-6,
        ),
        C_matrix=C_matrices_dict,
        iqa_energy_components={
            "T(A)": 75.03894204,
            "Vneen(A,A)/2 = Vne(A,A)": -183.63926895,
            "Vne(A,Mol)/2": -93.400150506,
            "Ven(A,Mol)/2": -96.344341721,
            "Vneen(A,Mol)/2": -189.74449223,
            "Vne(A,A')/2": -1.5805160326,
            "Ven(A,A')/2": -4.5247072473,
            "Vneen(A,A')/2": -6.1052232799,
            "Vee0(A,A) + Vee0(A,A')/2": 35.538139035,
            "Vee(A,A) + Vee(A,A')/2": 35.145962157,
            "VeeC(A,A) + VeeC(A,A')/2": 44.071057668,
            "VeeX0(A,A) + VeeX0(A,A')/2": -8.5329186324,
            "VeeX(A,A) + VeeX(A,A')/2": -8.9250955109,
            "Vnn(A,Mol)/2": 4.0753183136,
            "Vee0(A,A)": 33.972313611,
            "Vee(A,A)": 33.580136733,
            "VeeC(A,A)": 42.300500739,
            "VeeX0(A,A)": -8.3281871282,
            "VeeX(A,A)": -8.7203640066,
            "Vee0(A,A')/2": 1.5658254241,
            "Vee(A,A')/2": 1.5658254241,
            "VeeC(A,A')/2": 1.7705569283,
            "VeeX0(A,A')/2": -0.20473150425,
            "VeeX(A,A')/2": -0.20473150425,
            "V_IQA(A)": -150.52321176,
            "VC_IQA(A)": -141.59811625,
            "VX_IQA(A)": -8.9250955109,
            "V_IQA(A,A)": -150.05913221,
            "VC_IQA(A,A)": -141.33876821,
            "VX_IQA(A,A)": -8.7203640066,
            "V_IQA(A,A')/2": -0.46407954221,
            "VC_IQA(A,A')/2": -0.25934803796,
            "VX_IQA(A,A')/2": -0.20473150425,
            "E_IQA0(A)": -75.092092839,
            "E_IQA(A)": -75.484269717,
            "E_IQA_Intra0(A)": -74.628013297,
            "E_IQA_Intra(A)": -75.020190175,
            "E_IQA_Inter0(A)": -0.46407954221,
            "E_IQA_Inter(A)": -0.46407954221,
        },
        iqa=-7.5484269717e01,
        e_intra=-75.020190175,
        q=-1.0762060817,
        q00=-1.0762060817,
        dipole_mag=pytest.approx(0.2579226931234475),
        total_time=184,
    )
