from pathlib import Path

from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)


def submit_gjfs(directory):
    logger.info("Submitting gjfs to Gaussian")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript(SCRIPT_NAMES["gaussian"])
    for point in points:
        point.gjf.write()
        submission_script.add_command(GaussianCommand(point.gjf.path))
    submission_script.write()
    submission_script.submit()


def check_gaussian_output(gaussian_file: str):
    if Path(gaussian_file).with_suffix(".wfn").exists():
        print_completed()
    else:
        logger.error(f"Gaussian Job {gaussian_file} failed to run")
