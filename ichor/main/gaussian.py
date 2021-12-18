import sys
from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.common.io import last_line
from ichor.files import GJF, PointsDirectory
from ichor.log import logger
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)


def submit_points_directory_to_gaussian(
    directory: Path, overwrite_existing: bool = True, force: bool = False
) -> Optional[JobID]:
    """Function that writes out .gjf files from .xyz files that are in each directory and
    calls submit_gjfs which submits all .gjf files in a directory to Gaussian. Gaussian outputs .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    :param overwrite_existing: Whether to overwrite existing gjf files in a directory. Default is True.
        If this is False, then any existing `.gjf` files in the directory will not be overwritten
        (thus they would not be using the Gaussian settings from GLOBALS.)
    """
    points = PointsDirectory(
        directory
    )  # a directory which contains points (a bunch of molecular geometries)
    gjf_files = write_gjfs(points, overwrite_existing)
    return submit_gjfs(gjf_files, force=force)


def write_gjfs(
    points: PointsDirectory, overwrite_existing: bool
) -> List[Path]:
    """Writes out .gjf files in every PointDirectory which is contained in a PointsDirectory. Each PointDirectory should always have a `.xyz` file in it,
    which contains only one molecular geometry. This `.xyz` file can be used to write out the `.gjf` file in the PointDirectory (if it does not exist already).

    :param points: A PointsDirectory instance which wraps around a whole directory containing points (such as TRAINING_SET).
    :param overwrite_existing: Whether to overwrite existing gjf files in a directory. Default is True (see `submit_points_directory_to_gaussian`)
        If this is False, then any existing `.gjf` files in the directory will not be overwritten (thus they would not be using the GLOBALS Gaussian settings.)
    :return: A list of Path objects which point to `.gjf` files in each PointDirectory that is contained in the PointsDirectory.
    """
    gjfs = []
    for point in points:
        if not point.gjf.exists():
            point.gjf = GJF(
                Path(point.path / (point.path.name + GJF.filetype))
            )
        point.gjf.atoms = point.xyz.atoms

        if not point.gjf.exists() or overwrite_existing:
            point.gjf.write()

        gjfs.append(point.gjf.path)

    return gjfs


def submit_gjfs(
    gjfs: List[Path],
    force: bool = False,
    script_name: Optional[Path] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Function that writes out a submission script which contains an array of Gaussian jobs to be ran on compute nodes. If calling this function from
    a log-in node, it will write out the submission script, a datafile (file which contains the names of all the .gjf file that need to be ran through Gaussian),
    and it will submit the submission script to compute nodes as well to run Gaussian on compute nodes. However, if using this function from a compute node,
    (which will happen when ichor is ran in auto-run mode), this function will only be used to write out the datafile and will not submit any new jobs
    from the compute node (as you cannot submit jobs from compute nodes on CSF3.)

    :param gjfs: A list of Path objects pointing to .gjf files
    :param force: Run Gaussian calculations on given .gjf files, even if .wfn files already exist. Defaults to False.
    :script_name: Path to write submission script out to defaults to SCRIPT_NAMES["gaussian"]
    :param hold: An optional JobID for which this job to hold. This is used in auto-run to hold this job for the previous job to finish, defaults to None
    :return: The JobID of this job given by the submission system.
    """

    if script_name is None:
        script_name = SCRIPT_NAMES["gaussian"]

    # make a SubmissionScript instance which is going to house all the jobs that are going to be ran
    # the submission_script object can be accessed even after the context manager
    with SubmissionScript(script_name) as submission_script:
        for gjf in gjfs:
            if force or not gjf.with_suffix(".wfn").exists():
                submission_script.add_command(
                    GaussianCommand(gjf)
                )  # make a list of GaussianCommand instances.
                logger.debug(f"Adding {gjf} to {submission_script.path}")
    # write the final submission script file that containing the job that needs to be ran (could be an array job that has many tasks)
    if len(submission_script.commands) > 0:
        logger.info(
            f"Submitting {len(submission_script.commands)} GJF(s) to Gaussian"
        )
        # submit the final submission script to the queuing system, so that job is ran on compute nodes.
        return submission_script.submit(hold=hold)


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

    from ichor.common.io import mkdir, move
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.log import logger

    gaussian_file = Path(gaussian_file)
    wfn_file_path = Path(gaussian_file).with_suffix(".wfn")

    if gaussian_file.exists():

        # if the wfn file path does not exist or the "TOTAL ENERGY" is not in the last line of the .wfn file
        if (not wfn_file_path.exists()) or (
            not "TOTAL ENERGY" in last_line(wfn_file_path)
        ):

            point_dir_path = wfn_file_path.parent

            mkdir(FILE_STRUCTURE["gaussian_scrubbed_points"])
            # get the name of the directory only containing the .gjf file
            point_dir_name = wfn_file_path.parent.name
            # get the Path to the Parent directory
            new_path = (
                FILE_STRUCTURE["gaussian_scrubbed_points"] / point_dir_name
            )

            # if a point with the same name already exists in the SCRUBBED_POINTS directory, then add a ~ at the end
            # this can happen for example if Gaussian fails for two points with the exact same directory name (one from training set, one from validation set or sample pool)
            while new_path.exists():
                point_dir_name = point_dir_name + "~"
                new_path = (
                    FILE_STRUCTURE["gaussian_scrubbed_points"] / point_dir_name
                )

            # move to new path and record in logger
            move(point_dir_path, new_path)

            if not wfn_file_path.exists():
                logger.error(
                    f"Moved point directory {point_dir_path} to {new_path} because .wfn file was not produced."
                )
            elif not "TOTAL ENERGY" in last_line(wfn_file_path):
                logger.error(
                    f"Moved point directory {point_dir_path} to {new_path} because .wfn file did not have 'TOTAL_ENERGY' in last line."
                )

    # if a .gjf file does not exist, we also move the point. A .gjf file should exist because this function is called when Gaussian is being ran.
    else:
        logger.error(
            f"Gaussian .gjf file {gaussian_file} for which output needs to be checked does not exist."
        )

        point_dir_path = wfn_file_path.parent

        mkdir(FILE_STRUCTURE["gaussian_scrubbed_points"])
        # get the name of the directory only containing the .gjf file
        point_dir_name = wfn_file_path.parent.name
        # get the Path to the Parent directory
        new_path = FILE_STRUCTURE["gaussian_scrubbed_points"] / point_dir_name

        # if a point with the same name already exists in the SCRUBBED_POINTS directory, then add a ~ at the end
        # this can happen for example if Gaussian fails for two points with the exact same directory name (one from training set, one from validation set or sample pool)
        while new_path.exists():
            point_dir_name = point_dir_name + "~"
            new_path = (
                FILE_STRUCTURE["gaussian_scrubbed_points"] / point_dir_name
            )

        # move to new path and record in logger
        move(point_dir_path, new_path)
