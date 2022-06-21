from pathlib import Path
from typing import List, Optional
from ichor.core.files import INT
from ichor.core.files.geometry import GeometryFile
from ichor.core.itypes import T
from tests.atoms import _test_atoms_coords_optional
from tests.path import get_cwd
import numpy as np

example_dir = get_cwd(__file__) / "example_ints"

def _assert_val_optional(value: T, expected_value: Optional[T]):
    if expected_value is not None:
        assert value == expected_value

def _assert_np_array_optional(arr1: np.ndarray, expected_array: Optional[np.ndarray]):
    if expected_array is not None:
        np.allclose(arr1, expected_array)

def _test_int_no_json(
    int_file: Path,
    atom_name: str = None,
    atom_num: int = None,
    parent: Optional[GeometryFile] = None,
    json_path: Path = None,
    integration_error: float = None,
    iqa: float = None,
    original_multipoles: dict = None,
    original_multipoles_without_q00: dict = None,
    rotated_multipoles: Optional[dict] = None,
    rotated_multipoles_without_q00: Optional[dict] = None,
    e_intra: float = None,
    q: float = None,
    q00: float = None,
    dipole: float = None,
    C: np.ndarray = None,
    rotated_dipole: dict = None,
    rotated_quadrupole: dict = None,
    rotated_octupole: dict = None,
    rotated_hexadecapole: dict = None
):
    """ Tests original .int file from AIMALL is being read in correctly. No json
    file is generated. json is checked in another test."""

    int_file = INT(int_file, parent, create_json=False, read_data_from_json=False)

    _assert_val_optional(int_file.atom_name, atom_name)
    _assert_val_optional(int_file.atom_num, atom_num)
    _assert_val_optional(int_file.json_path, json_path)
    _assert_val_optional(int_file.integration_error, integration_error)
    _assert_val_optional(int_file.iqa, iqa)
    _assert_val_optional(int_file.original_multipoles, original_multipoles)
    _assert_val_optional(int_file.original_multipoles_without_q00, original_multipoles_without_q00)
    _assert_val_optional(int_file.e_intra, e_intra)
    _assert_val_optional(int_file.q, q)
    _assert_val_optional(int_file.q00, q00)
    _assert_val_optional(int_file.dipole, dipole)

    if parent is not None:
        _assert_val_optional(int_file.parent, parent)
        _assert_np_array_optional(int_file.C, C)
        _assert_val_optional(int_file.rotated_multipoles, rotated_multipoles)
        _assert_val_optional(int_file.rotated_multipoles_without_q00, rotated_multipoles_without_q00)
        _assert_val_optional(int_file.rotated_dipole, rotated_dipole)
        _assert_val_optional(int_file.rotated_quadrupole, rotated_quadrupole)
        _assert_val_optional(int_file.rotated_octupole, rotated_octupole)
        _assert_val_optional(int_file.rotated_hexadecapole, rotated_hexadecapole)

def test_no_parent_int():

    _test_int_no_json(
        int_file=example_dir / "o1.int",
        atom_name="O1",
        atom_num=1,
        parent=None,
        json_path=example_dir / "o1.json",
        integration_error=-4.0077877571e-05,
        iqa=-7.5484269717e+01,
        original_multipoles={'original_q10': -0.020646892538, 'original_q11c': -0.0016461566576, 'original_q11s': -0.25708969568, 'original_q20': -0.021700469782, 'original_q21c': -0.75018382635, 'original_q21s': 0.017792037022, 'original_q22c': -0.16232546581, 'original_q22s': 0.065122302165, 'original_q30': 0.044683217585, 'original_q31c': -0.089287472207, 'original_q31s': 0.30596239543, 'original_q32c': -0.063395331291, 'original_q32s': -1.391653952, 'original_q33c': -0.067954891804, 'original_q33s': 0.20594440588, 'original_q40': -1.9609913177, 'original_q41c': 1.1488477959, 'original_q41s': 0.26702238434, 'original_q42c': -0.75531442849, 'original_q42s': -0.39080307859, 'original_q43c': 3.6310817472, 'original_q43s': -0.24247145429, 'original_q44c': -1.7369385615, 'original_q44s': 0.072615449798, 'q00': -1.0762060817},
        original_multipoles_without_q00={'original_q10': -0.020646892538, 'original_q11c': -0.0016461566576, 'original_q11s': -0.25708969568, 'original_q20': -0.021700469782, 'original_q21c': -0.75018382635, 'original_q21s': 0.017792037022, 'original_q22c': -0.16232546581, 'original_q22s': 0.065122302165, 'original_q30': 0.044683217585, 'original_q31c': -0.089287472207, 'original_q31s': 0.30596239543, 'original_q32c': -0.063395331291, 'original_q32s': -1.391653952, 'original_q33c': -0.067954891804, 'original_q33s': 0.20594440588, 'original_q40': -1.9609913177, 'original_q41c': 1.1488477959, 'original_q41s': 0.26702238434, 'original_q42c': -0.75531442849, 'original_q42s': -0.39080307859, 'original_q43c': 3.6310817472, 'original_q43s': -0.24247145429, 'original_q44c': -1.7369385615, 'original_q44s': 0.072615449798},
        rotated_multipoles=None,
        rotated_multipoles_without_q00=None,
        e_intra=-75.020190175,
        q=-1.0762060817,
        q00=-1.0762060817,
        dipole=0.2579226931234475,
        C=None,
        rotated_dipole=None,
        rotated_quadrupole=None,
        rotated_octupole=None,
        rotated_hexadecapole=None
    )
