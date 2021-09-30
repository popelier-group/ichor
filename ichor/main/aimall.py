import sys
from pathlib import Path
from typing import List, Optional

from ichor import constants
from ichor.batch_system import JobID
from ichor.files import PointsDirectory
from ichor.logging import logger
from ichor.submission_script import (SCRIPT_NAMES, AIMAllCommand,
                                     SubmissionScript, print_completed)


def submit_points_directory_to_aimall(
    directory: Path, atoms: Optional[List[str]] = None
) -> Optional[JobID]:
    """Submits .wfn files which will be partitioned into .int files by AIMALL. Each topological atom i the system has its own .int file"""

    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    wfns = check_wfns(points)
    return submit_wfns(wfns, atoms)


def check_wfns(points: PointsDirectory) -> List[Path]:
    wfns = []
    for point in points:
        if point.wfn.exists():
            point.wfn.check_header()
            wfns.append(point.wfn.path)
    return wfns


def submit_wfns(wfns: List[Path], atoms: Optional[List[str]] = None, force: bool = False, hold: Optional[JobID] = None) -> Optional[JobID]:
    with SubmissionScript(SCRIPT_NAMES["aimall"]) as submission_script:
        for wfn in wfns:
            if force or not wfn.with_suffix('.aim').exists():
                submission_script.add_command(
                    AIMAllCommand(wfn, atoms=atoms)
                )
    if len(submission_script.commands) > 0:
        # todo this will get executed when running from a compute node, but this does not submit any wfns to aimall, it is just used to make the datafile.
        logger.info(
            f"Submitting {len(submission_script.commands)} WFN(s) to AIMAll"
        )
        return submission_script.submit(hold=hold)


def rerun_aimall(wfn_file: str):
    # AIMAll deletes this sh file when it has successfully completed
    # If this file still exists then something went wrong
    if not wfn_file:
        print_completed()
        sys.exit()
    # logger.debug(f"Checking {wfn_file}")
    if not Path(wfn_file).with_suffix(".sh").exists():
        # logger.debug(f"AIMAll finished")
        print_completed()
    # else:
    #     logger.error(f"AIMAll Job {wfn_file} failed to run")


def scrub_aimall(wfn_file: str):
    """ Used by `CheckManager`. Checks if AIMALL job ran correctly. If it did not, it will move the Point to the `FILE_STRUCTURE["aimall_scrubbed_points"]`
    directory and record that it has moved the point in the log file. If a .sh file exists and the integration error for the point is lower than the
    GLOBALS-specified threshold, then this checking function will not do anything.
    
    :param wfn_file: A string that is a Path to a .gjf file
    """

    from ichor.common.io import mkdir, move
    from ichor.logging import logger
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.files.point_directory import PointDirectory
    from ichor.globals import GLOBALS

    if wfn_file:

        # AIMAll deletes this sh file when it has successfully completed
        sh_file_path = Path(wfn_file).with_suffix(".sh")

        # get the name of the directory only containing the .wfn file
        point_dir_path = sh_file_path.parent
        point_dir_name = point_dir_path.name  # returns the name of the directory, eg. WATER0001, WATER0002, etc.

        n_integration_error = 0
        point = PointDirectory(point_dir_path)

        # find atoms which have large AIMALL integration error
        if point.ints:
            integration_errors = point.integration_error
            for atom, integration_error in integration_errors.items():
                if (
                    abs(integration_error)
                    > GLOBALS.INTEGRATION_ERROR_THRESHOLD
                ):
                    logger.warning(f"{point_dir_path} | {atom} | Integration Error: {integration_error}")
                    n_integration_error += 1

        # if the .sh file exists or there is an atom with large integration error
        if (sh_file_path.exists() or n_integration_error > 0):

            if GLOBALS.SCRUB_POINTS:

                    mkdir(FILE_STRUCTURE["aimall_scrubbed_points"])
                    new_path = FILE_STRUCTURE["aimall_scrubbed_points"] / point_dir_name

                    # if a point with the same name already exists in the SCRUBBED_POINTS directory, then add a ~ at the end
                    # this can happen for example if aimall fails for two points with the exact same directory name (one from training set, one from validation set or sample pool)
                    while new_path.exists():
                        point_dir_name = point_dir_name + "~"
                        new_path = FILE_STRUCTURE["aimall_scrubbed_points"] / point_dir_name

                    # move to new path and record in logger
                    move(point_dir_path, new_path)

                    if sh_file_path.exists():
                        logger.error(f"Moved point directory {point_dir_path} to {new_path} because it failed to run.")
                    elif n_integration_error > 0:
                        logger.error(f"Moved point directory {point_dir_path} to {new_path} because integration error for atom was greater than {GLOBALS.INTEGRATION_ERROR_THRESHOLD}.")

            else:
                logger.warning(
                    f"{n_integration_error} atoms are above the integration error threshold ({GLOBALS.INTEGRATION_ERROR_THRESHOLD}), consider removing these points or increasing precision"
                )