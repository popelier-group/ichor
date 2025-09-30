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
def submit_single_mtd_xyz(
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
    mtd_parent = Path(ichor.hpc.global_variables.FILE_STRUCTURE["mtd_traj"])
    mkdir(mtd_parent)

    # subfolder for running calc
    mtd_dir = Path(mtd_parent / system_name)
    mkdir(mtd_dir)
    
    # copy xyz trajectory into mtd folder (copy to make sure opt xyz not overwritten)
    try:
        shutil.copy(input_xyz_traj, mtd_dir)
    except:
        if overwrite:
            try:
                rm_path = mtd_dir
                shutil.rmtree(rm_path)
                mkdir(mtd_dir)
                shutil.copy(input_xyz_traj, mtd_dir)
            except:
                print("FILE DOES NOT EXIST FOR OVERWRITE. RUNNING AS NORMAL")
                pass
        else:
            print("ERROR, FILE EXISTS AND OVERWRITE WAS NOT SELECTED. ABORTING")
            return
        
    #submit_mtd_calc_to_plumed(
    #    mtd_directory=mtd_dir,
    #    input_xyz_path=input_xyz_path,
    #    ncores=ncores,
    #    hold=hold,
    #    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
    #    / input_xyz_path.name
    #    / "MTD",
    #    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
    #    / input_xyz_path.name
    #    / "MTD",) 

def submit_mtd_calc_to_plumed(
    mtd_directory: Path,
    ncores=2,
    hold: JobID = None,
    script_name: str = ichor.hpc.global_variables.SCRIPT_NAMES["mtd"],
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out XTB input files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .xyz files in a directory to ASE.

    :param directory: A Path object which is the path of the directory
        (commonly traning set path, sample pool path, etc.).
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written gjf files (overwriting
        settings from previously existing gjf files)
    """

    mtd_files = write_mtd_input(mtd_directory, **kwargs)
    return submit_mtd(
        mtd_files,
        script_name=script_name,
        ncores=ncores,
        hold=hold,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    )

def write_mtd_input(mtd_directory: Path, **kwargs) -> List[Path]:
##### THIS PART NEEDS WORK!
    mtds = []
    return mtds

def submit_mtd(
    mtds: List[Path],
    script_name: Optional[Union[str, Path]] = ichor.hpc.global_variables.SCRIPT_NAMES[
        "mtd"
    ],
    hold: Optional[JobID] = None,
    ncores=2,
    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"],
    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"],
) -> JobID:
    """Function that writes out a submission script which contains an array of
    mtd jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of
    all the .xyz file that need to be ran through PLUMED),
    and it will submit the submission script to compute nodes as well to run PLUMED on compute nodes.
    However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
    the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param xyz: A list of Path objects pointing to .xyz files
    :script_name: Path to write submission script out to defaults to ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold.
        This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        number_of_jobs = 0

        for mtd in mtds:
            submission_script.add_command(PythonCommand(mtd))
            number_of_jobs += 1

        ichor.hpc.global_variables.LOGGER.info(
            f"Added {number_of_jobs} / {len(mtds)} PLUMED metadynamics jobs to {submission_script.path}"
        )

    # submit on compute node if there are files to submit
    if len(submission_script.grouped_commands) > 0:
        ichor.hpc.global_variables.LOGGER.info(
            f"Submitting {len(submission_script.grouped_commands)} metadynamics(s) to PLUMED"
        )
        return submission_script.submit(hold=hold)
    else:
        raise ValueError("There are no jobs to submit in the submission script.")
