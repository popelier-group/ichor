from pathlib import Path
from typing import Dict

from ichor.core.files import AIM
from ichor.core.files.aimall.aim import AimAtom
from ichor.core.common.types import Version
from ichor.core.common.types.itypes import T
from tests.path import get_cwd
from tests.test_files import _assert_val_optional

import pytest

example_dir = get_cwd(__file__) / "example_aims"

def _assert_version(
        aim_version: Version,
        reference_version: Version
    ):
    assert aim_version.major == reference_version.major
    assert aim_version.minor == reference_version.minor
    assert aim_version.patch == reference_version.patch
    assert aim_version.revision == reference_version.revision
    
def _assert_aim_atoms(
        aim_file_atoms: Dict[str, AimAtom],
        reference_aim_atoms: Dict[str, AimAtom]
    ):
    # compare the aim atom attributes to reference values
    for reference_aim_atom_name, reference_aim_atom in reference_aim_atoms.items():
        assert aim_file_atoms[reference_aim_atom_name].atom_name == reference_aim_atom.atom_name
        assert aim_file_atoms[reference_aim_atom_name].inp_file == reference_aim_atom.inp_file
        assert aim_file_atoms[reference_aim_atom_name].int_file == reference_aim_atom.int_file
        assert aim_file_atoms[reference_aim_atom_name].time_taken == reference_aim_atom.time_taken
        assert aim_file_atoms[reference_aim_atom_name].integration_error == pytest.approx(reference_aim_atom.integration_error)

def _test_read_aim(
    aim_path: Path,
    license_check_succeeded: bool = None,
    version: Version = None,
    wfn_path: Path = None,
    extout_path: Path = None,
    mgp_path: Path = None,
    sum_path: Path = None,
    sumviz_path: Path = None,
    nproc: int = None,
    nacps: int = None,
    nnacps: int = None,
    nbcps: int = None,
    nrcps: int = None,
    nccps: int = None,
    output_file: Path = None,
    cwd: Path = None,
    reference_aim_atoms: Dict[str, AimAtom] = None
):
    
    aim = AIM(aim_path)
    
    _assert_val_optional(aim.license_check_succeeded, license_check_succeeded)
    _assert_version(aim.version, version)
    _assert_val_optional(aim.wfn_path, wfn_path)
    _assert_val_optional(aim.extout_path, extout_path)
    _assert_val_optional(aim.mgp_path, mgp_path)
    _assert_val_optional(aim.sum_path, sum_path)
    _assert_val_optional(aim.sumviz_path, sumviz_path)
    _assert_val_optional(aim.nproc, nproc)
    _assert_val_optional(aim.nacps, nacps)
    _assert_val_optional(aim.nnacps, nnacps)
    _assert_val_optional(aim.nbcps, nbcps)
    _assert_val_optional(aim.nrcps, nrcps)
    _assert_val_optional(aim.nccps, nccps)
    _assert_val_optional(aim.output_file, output_file)
    _assert_val_optional(aim.cwd, cwd)
    _assert_aim_atoms(aim, reference_aim_atoms)
    
def test_water_monomer_aim():
    
    aim_file_path = get_cwd(__file__) / "example_aims" / "WATER_MONOMER0001.aim"
    reference_version = Version("19.10.12")
    
    reference_aim_atoms = {"O1":
        AimAtom("O1", Path("WATER_MONOMER0001_atomicfiles/o1.inp"),
                Path("WATER_MONOMER0001_atomicfiles/o1.int"),
                184,
                -4e-05
                )
                           }
    
    _test_read_aim(
        aim_path=aim_file_path,
        license_check_succeeded = True,
        version = reference_version,
        wfn_path = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001/WATER_MONOMER0001.wfn"),
        extout_path = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001/WATER_MONOMER0001.extout"),
        mgp_path = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001/WATER_MONOMER0001.mgp"),
        sum_path = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001/WATER_MONOMER0001.sum"),
        sumviz_path = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001/WATER_MONOMER0001.sumviz"),
        nproc = 2,
        nacps = 3,
        nnacps = 0,
        nbcps = 2,
        nrcps = 0,
        nccps = 0,
        output_file = Path("WATER_MONOMER0001_atomicfiles/o1.int"),
        cwd = Path("/net/scratch2/mbdxwym4/water_monomer_active_learning/ATOMS/O1/TRAINING_SET/WATER_MONOMER0001"),
        reference_aim_atoms = reference_aim_atoms
    )