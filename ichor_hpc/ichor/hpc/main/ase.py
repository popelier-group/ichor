from pathlib import Path
import shutil
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.files import GJF, PointsDirectory, WFN
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import GaussianCommand
from ichor.hpc.submission_script import SubmissionScript
from ichor.core.common.io import mkdir


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


## function for making plumed folder work with points dir

## function for creating plumed job file

## function for submitting job file to queue
