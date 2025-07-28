import shutil
from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir

from ichor.core.files import PointsDirectory, XTB, XYZ
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import GaussianCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_single_ase_xyz(
    input_xyz_path: Union[str, Path],
    ncores=2,
    keywords=["opt"],
    method="b3lyp",
    basis_set="6-31+g(d,p)",
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:

    input_xyz_path = Path(input_xyz_path)
    mkdir(ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"])
    opt_dir = ichor.hpc.global_variables.FILE_STRUCTURE["optimised_geoms"]
    shutil.copy(input_xyz_path, opt_dir)

    submit_points_directory_to_ase(
        points_directory=opt_dir,
        overwrite_existing=True,
        force_calculate_wfn=False,
        ncores=ncores,
        method=method,
        basis_set=basis_set,
        outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        / input_xyz_path.name
        / "ASE",
        errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
        / input_xyz_path.name
        / "ASE",
        keywords=keywords,
    )


# function for making plumed folder work with points dir
def submit_points_directory_to_ase(
    points_directory: Union[Path, PointsDirectory],
    overwrite_existing=False,
    force_calculate_wfn: bool = False,
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:

    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    gjf_files = write_gjfs(points_directory, overwrite_existing, **kwargs)
    return submit_gjfs(
        gjf_files,
        script_name=script_name,
        force_calculate_wfn=force_calculate_wfn,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )


# function for creating plumed job file

# function for submitting job file to queue
