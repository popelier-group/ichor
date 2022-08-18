# from tests.test_files.test_read_gjf import _test_read_gjf
# from tests.test_files.test_read_int import _test_int
# from tests.test_files.test_read_wfn import _test_read_wfn, _test_molecular_orbitals
# from tests.test_files.test_read_aim import _test_read_aim
# from tests.test_files.test_read_gau import _test_read_gau, _assert_atomic_forces
# from tests.test_atoms import _test_atoms_coords

# from pathlib import Path
# from typing import Dict, Optional, List
# from ichor.core.files import PointDirectory
# from ichor.core.files.aimall.aim import AimAtom
# from ichor.core.common.types import Version
# from ichor.core.common.types.itypes import T
# from tests.path import get_cwd
# from tests.test_files import _assert_val_optional
# from ichor.core.atoms import Atoms


# def _test_point_directory(
#     point_dir_path = Path
#     ):
    
#     point_dir_inst = PointDirectory(point_dir_path)
    
#     gjf_path = point_dir_inst.gjf.path
#     gaussian_out_path = point_dir_inst.gaussian_out.path
#     xyz_path = point_dir_inst.xyz.path
#     ints_path = point_dir_inst.ints.path
#     aim_path = point_dir_inst.aim.path
    
#     def _test_read_gjf(
#         gjf_file: Path,
#         link0: Optional[List[str]] = None,
#         method: Optional[str] = None,
#         basis_set: Optional[str] = None,
#         keywords: Optional[List[str]] = None,
#         title: Optional[str] = None,
#         charge: Optional[int] = None,
#         spin_multiplicity: Optional[int] = None,
#         atoms: Optional[Atoms] = None,
#     ):
