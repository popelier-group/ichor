from pathlib import Path
import sys

from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)
from ichor.batch_system import JobID
from typing import Optional


def submit_gjfs(directory) -> Optional[JobID]:
    points = PointsDirectory(directory)
    submission_script = SubmissionScript(SCRIPT_NAMES["gaussian"])
    for point in points:
        if not point.gjf.path.with_suffix(".wfn").exists():
            point.gjf.write()
            submission_script.add_command(GaussianCommand(point.gjf.path))
    logger.info(f"Submitting {len(submission_script.commands)} GJF(s) to Gaussian")
    submission_script.write()
    return submission_script.submit()


def check_gaussian_output(gaussian_file: str):
    if not gaussian_file:
        print_completed()
        sys.exit()
    if Path(gaussian_file).with_suffix(".wfn").exists():
        print_completed()
    else:
        logger.error(f"Gaussian Job {gaussian_file} failed to run")
