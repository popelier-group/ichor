import sys
from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.common.io import last_line
from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)


def submit_gjfs(directory: Path) -> Optional[JobID]:
    """Function that submits all .gjf files in a directory to Gaussian, which will output .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    """
    points = PointsDirectory(
        directory
    )  # a directory which contains points (a bunch of molecular geometries)
    # make a SubmissionScript instance which is going to house all the jobs that are going to be ran
    submission_script = SubmissionScript(SCRIPT_NAMES["gaussian"])
    for point in points:  # point is an instance of PointDirectory
        if not point.gjf.path.with_suffix(".wfn").exists():
            point.gjf.write()  # write out the .gjf files which are input to Gaussian to ensure correct formatting
            submission_script.add_command(
                GaussianCommand(point.gjf.path)
            )  # make a list of GaussianCommand instances.
            logger.debug(
                f"Adding {point.gjf.path} to {SCRIPT_NAMES['gaussian']}"
            )
    logger.info(
        f"Submitting {len(submission_script.commands)} GJF(s) to Gaussian"
    )
    # write the final submission script file that containing the job that needs to be ran (could be an array job that has many tasks)
    submission_script.write()
    # submit the final submission script to the queuing system, so that job is ran on compute nodes.
    return submission_script.submit()


def check_gaussian_output(gaussian_file: str):
    """Checks if Gaussian jobs ran correctly and a full .wfn file is returned. If there is no .wfn file or it does not
    have the correct contents, then rerun Gaussian."""
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
