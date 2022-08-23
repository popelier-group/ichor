import sys
from pathlib import Path
from typing import List, Optional

from ichor.core.common.io import last_line
from ichor.core.files import GJF, PointsDirectory, PointDirectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.log import logger
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    GaussianCommand,
    SubmissionScript,
    print_completed,
)
from ichor.hpc.log import logger
from typing import Union

def submit_points_directory_to_gaussian(
    directory: Union[Path, PointsDirectory], overwrite_existing_gjf: bool = True, force_calculate_wfn: bool = False,
    rerun: bool = False, scrub: bool = False, ncores=2,**kwargs) -> Optional[JobID]:
    """Function that writes out .gjf files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .gjf files in a directory to Gaussian. Gaussian outputs .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    :param overwrite_existing: Whether to overwrite existing gjf files in a directory. Default is True.
        If this is False, then any existing `.gjf` files in the directory will not be overwritten
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files, even if .wfn files already exist. Defaults to False.
    :param rerun: Whether to attempt to rerun failed points. Default False
    :param scrub: Whether to scrub (move) failed points to another directory for scrubbed points. Default False
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc. These will get used if overwrite_existing_gjf is True or if the gjf path does
        not exist yet.
    """
    if not isinstance(directory, PointsDirectory):
        points_directory = PointsDirectory(
            directory
        )  # a directory which contains points (a bunch of molecular geometries)
    gjf_files = write_gjfs(points_directory, overwrite_existing_gjf, **kwargs)
    return submit_gjfs(gjf_files, force_calculate_wfn=force_calculate_wfn, rerun_points=rerun, scrub_points=scrub, ncores=ncores)


def write_gjfs(
    points_directory: PointsDirectory, overwrite_existing_gjf: bool, **kwargs) -> List[Path]:
    """Writes out .gjf files in every PointDirectory which is contained in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the `.gjf` file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a whole directory containing points (such as TRAINING_SET).
    :param overwrite_existing: Whether to overwrite existing gjf files in a directory. Default is True (see `submit_points_directory_to_gaussian`)
        If this is False, then any existing `.gjf` files in the directory will not be overwritten (thus they would not be using the GLOBALS Gaussian settings.)
    :return: A list of Path objects which point to `.gjf` files in each PointDirectory that is contained in the PointsDirectory.
    """

    gjfs = []
    
    for point_directory in points_directory:
        
        # use key word arguments to make gjf if gjf file does not exist or overwrite_existing flag is set
        if not point_directory.gjf.exists() or overwrite_existing_gjf:
            point_directory.gjf = GJF(
                Path(point_directory.path / (point_directory.path.name + GJF.filetype)), **kwargs)
        # if gjf path exists or overwrite_existing_gjf is False, then do not modify existing GJF file.
        else:
            point_directory.gjf = GJF(Path(point_directory.path / (point_directory.path.name + GJF.filetype)))
        point_directory.gjf.atoms = point_directory.xyz.atoms

        gjfs.append(point_directory.gjf.path)

    return gjfs

def submit_gjfs(
    gjfs: List[Path],
    force_calculate_wfn: bool = False,
    script_name: Optional[Path] = SCRIPT_NAMES["gaussian"],
    hold: Optional[JobID] = None,
    rerun = False,
    scrub = False,
    ncores = 2,
) -> Optional[JobID]:
    """Function that writes out a submission script which contains an array of Gaussian jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of all the .gjf file that need to be ran through Gaussian),
    and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes. However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param gjfs: A list of Path objects pointing to .gjf files
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files, even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold. This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(script_name, ncores=ncores) as submission_script:
        for gjf in gjfs:
            # append to submission script if we want to rerun the calculation (even if wfn file exits) or a wfn file does not exist
            if force_calculate_wfn or not gjf.with_suffix(".wfn").exists():
                submission_script.add_command(
                    GaussianCommand(gjf, rerun=rerun, scrub=scrub)
                )  # make a list of GaussianCommand instances.
                logger.debug(f"Adding {gjf} to {submission_script.path}")
    # write the final submission script file that containing the job that needs to be ran (could be an array job that has many tasks)
    logger.info(
        f"Submitting {len(submission_script.commands)} GJF(s) to Gaussian"
    )
    # submit the final submission script to the queuing system, and return the job id. hold for other jobs if needed.
    return submission_script.submit(hold=hold)

# Below are functions used by autorun to check if stuff exists and reruns if necessary.

def rerun_gaussian(gaussian_file: str):
    """Used by `CheckManager`. Checks if Gaussian jobs ran correctly and a full .wfn file is returned. If there is no .wfn file or it does not
    have the correct contents, then rerun Gaussian.

    :param gaussian_file: A string that is a Path to a .gjf file
    """
    if not gaussian_file:
        print_completed()
        sys.exit()
    if Path(gaussian_file).with_suffix(
        ".wfn"
    ).exists() and "TOTAL ENERGY" in last_line(
        Path(gaussian_file).with_suffix(".wfn")
    ):
        print_completed()
    else:
        logger.error(f"Gaussian Job {gaussian_file} failed to run")


def scrub_gaussian(gaussian_file: str):
    """Used by `CheckManager`. Checks if Gaussian job ran correctly. If it did not, it will move the Point to the `FILE_STRUCTURE["gaussian_scrubbed_points"]` directory
    and record that it has moved the point in the log file. If a .wfn file exists and it contains the correct information in its last line, then
    this checking function will not do anything.

    :param gaussian_file: A string that is a Path to a .gjf file
    """

    gaussian_file = Path(gaussian_file)
    point = PointDirectory(gaussian_file.parent)

    reason: Optional[str] = None
    if not gaussian_file.exists():
        reason = f"{gaussian_file} does not exist"
    elif not point.wfn.exists():
        reason = f"No WFN file found in directory {point.path}"
    elif "TOTAL ENERGY" not in last_line(point.wfn.path):
        reason = f"Incomplete WFN ('{point.wfn.path}') file found"

    if reason is not None:
        logger.error(f"'{point.path}' will be ignored | Reason: {reason}")
        point.ignore(reason)
