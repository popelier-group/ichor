from pathlib import Path
from typing import List, Optional, Union

from ichor.core.files import GJF, PointsDirectory
from ichor.hpc import SCRIPT_NAMES
from ichor.hpc.batch_system import JobID
from ichor.hpc.log import logger
from ichor.hpc.submission_script import GaussianCommand, SubmissionScript


def submit_points_directory_to_gaussian(
    points_directory: Union[Path, PointsDirectory],
    overwrite_existing=False,
    force_calculate_wfn: bool = False,
    ncores=2,
    rerun: bool = False,
    scrub: bool = False,
    hold: JobID = None,
    script_name: str = SCRIPT_NAMES["gaussian"],
    **kwargs,
) -> Optional[JobID]:
    """Function that writes out .gjf files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .gjf files in a directory to Gaussian. Gaussian outputs .wfn files.

    :param directory: A Path object which is the path of the directory
        (commonly traning set path, sample pool path, etc.).
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
        even if .wfn files already exist. Defaults to False.
    :param rerun: Whether to attempt to rerun failed points. Default False
    :param scrub: Whether to scrub (move) failed points to another directory for scrubbed points. Default False
    :param kwargs: Key word arguments to pass to GJF class. These are things like number of cores, basis set,
        level of theory, spin multiplicity, charge, etc.
        These will get used in the new written gjf files (overwriting
        settings from previously existing gjf files)
    """
    # a directory which contains points (a bunch of molecular geometries)
    if not isinstance(points_directory, PointsDirectory):
        points_directory = PointsDirectory(points_directory)

    gjf_files = write_gjfs(points_directory, overwrite_existing, **kwargs)
    return submit_gjfs(
        gjf_files,
        script_name=script_name,
        force_calculate_wfn=force_calculate_wfn,
        rerun=rerun,
        scrub=scrub,
        ncores=ncores,
        hold=hold,
    )


def write_gjfs(
    points_directory: PointsDirectory, overwrite_existing: bool, **kwargs
) -> List[Path]:
    """Writes out .gjf files in every PointDirectory which is contained
    in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the `.gjf`
    file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a
        whole directory containing points (such as TRAINING_SET).
    :return: A list of Path objects which point to `.gjf` files in each
        PointDirectory that is contained in the PointsDirectory.
    """

    gjfs = []

    for point_directory in points_directory:

        if overwrite_existing:
            # the gjf file object might not exist, so check for that first
            if point_directory.gjf:
                # if the object exists, then delete it
                point_directory.gjf.path.unlink()
        point_directory.gjf = GJF(
            Path(point_directory.path / (point_directory.path.name + GJF.filetype)),
            **kwargs,
        )
        point_directory.gjf.atoms = point_directory.xyz.atoms
        point_directory.gjf.write()

        gjfs.append(point_directory.gjf.path)

    return gjfs


def submit_gjfs(
    gjfs: List[Path],
    force_calculate_wfn: bool = False,
    script_name: Optional[Union[str, Path]] = SCRIPT_NAMES["gaussian"],
    hold: Optional[JobID] = None,
    rerun=False,
    scrub=False,
    ncores=2,
) -> JobID:
    """Function that writes out a submission script which contains an array of
    Gaussian jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of
    all the .gjf file that need to be ran through Gaussian),
    and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes.
    However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out
    the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param gjfs: A list of Path objects pointing to .gjf files
    :param force_calculate_wfn: Run Gaussian calculations on given .gjf files,
        even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold.
        This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    # make a SubmissionScript instance which is going to contain all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(script_name, ncores=ncores) as submission_script:
        for gjf in gjfs:
            # append to submission script if we want to rerun the calculation
            # (even if wfn file exits) or a wfn file does not exist
            if force_calculate_wfn or not gjf.with_suffix(".wfn").exists():
                submission_script.add_command(
                    GaussianCommand(gjf, rerun=rerun, scrub=scrub)
                )  # make a list of GaussianCommand instances.
                logger.info(f"Adding {gjf} to {submission_script.path}")

    # todo this will get executed when running from a compute node, but this does not
    # submit any wfns to aimall, it is just used to make the datafile.
    if len(submission_script.grouped_commands) > 0:
        logger.info(
            f"Submitting {len(submission_script.grouped_commands)} GJF(s) to Gaussian"
        )
        return submission_script.submit(hold=hold)
    else:
        raise ValueError("There are no jobs to submit in the submission script.")


# Below are functions used by autorun to check if stuff exists and reruns if necessary.

# def rerun_gaussian(gaussian_file: str):
#     """Used by `CheckManager`. Checks if Gaussian jobs ran correctly and a full .wfn
#     file is returned. If there is no .wfn file or it does not
#     have the correct contents, then rerun Gaussian.

#     :param gaussian_file: A string that is a Path to a .gjf file
#     """
#     if not gaussian_file:
#         print_completed()
#         sys.exit()
#     if Path(gaussian_file).with_suffix(".wfn").exists() and "TOTAL ENERGY" in last_line(
#         Path(gaussian_file).with_suffix(".wfn")
#     ):
#         print_completed()
#     else:
#         logger.error(f"Gaussian Job {gaussian_file} failed to run")


# def scrub_gaussian(gaussian_file: str):
#     """Used by `CheckManager`. Checks if Gaussian job ran correctly.
#     If it did not, it will move the Point to the `FILE_STRUCTURE["gaussian_scrubbed_points"]` directory
#     and record that it has moved the point in the log file. If a .wfn file exists
#     and it contains the correct information in its last line, then
#     this checking function will not do anything.

#     :param gaussian_file: A string that is a Path to a .gjf file
#     """

#     gaussian_file = Path(gaussian_file)
#     point = PointDirectory(gaussian_file.parent)

#     reason: Optional[str] = None
#     if not gaussian_file.exists():
#         reason = f"{gaussian_file} does not exist"
#     elif not point.wfn.exists():
#         reason = f"No WFN file found in directory {point.path}"
#     elif "TOTAL ENERGY" not in last_line(point.wfn.path):
#         reason = f"Incomplete WFN ('{point.wfn.path}') file found"

#     if reason is not None:
#         logger.error(f"'{point.path}' will be ignored | Reason: {reason}")
#         point.ignore(reason)
