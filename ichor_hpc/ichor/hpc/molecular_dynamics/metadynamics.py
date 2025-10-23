from pathlib import Path
import shutil
from typing import List, Optional, Union

import ichor.hpc.global_variables
from ichor.core.common.io import mkdir
from ichor.core.files import Trajectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


## set up folder for running mtd calculation
def prep_mtd(
    input_xyz_path: Union[str, Path],
    ncores=2,
    overwrite=False,
    hold: JobID = None,
    **kwargs,
) -> Optional[JobID]:
    
    # input trajectory
    input_xyz_traj = Trajectory(input_xyz_path)
    system_name = input_xyz_path.stem

    # metadynamics parent folder
    mtd_parent = Path(ichor.hpc.global_variables.FILE_STRUCTURE["metadynamics_traj"])
    mkdir(mtd_parent)

    # subfolder for running calc
    mtd_dir = Path(mtd_parent / system_name)
    dest_name = Path(mtd_dir / input_xyz_path.name)
    
    if overwrite:
        try:
            rm_path = mtd_dir
            shutil.rmtree(rm_path)
            mkdir(mtd_dir)
            shutil.copy(input_xyz_path, mtd_dir)
        except:
            print("FILE DOES NOT EXIST FOR OVERWRITE. RUNNING AS NORMAL")
            pass
    # if not set to overwrite and file exits
    elif not overwrite and dest_name.exists():
        print("ERROR, FILE EXISTS AND OVERWRITE WAS NOT SELECTED. ABORTING")
        return
    # copy normally
    else:
        mkdir(mtd_dir)
        shutil.copy(input_xyz_path, mtd_dir)

    # build mtd script here
    #dataset_input_script = DatasetPrepScript(
    #    Path(input_file_path),
    #    outlier_input_dir=Path(outlier_input_dir),
    #    **kwargs,
    #)
    #dataset_input_script.write()
    #return dataset_input_script.path
        

def submit_mtd(input_script: Path,
    script_name: Optional[Union[str, Path]],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> JobID:
    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        submission_script.add_command(PythonCommand(input_script))

    return submission_script.submit(hold=hold)