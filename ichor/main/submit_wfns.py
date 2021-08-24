from pathlib import Path
from typing import Optional, List

from ichor import constants
from ichor.batch_system import JobID
from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, AIMAllCommand,
                                     SubmissionScript, print_completed)


def submit_wfns(directory: Path, atoms: Optional[List[str]]) -> Optional[JobID]:
    """ Submits .wfn files which will be partitioned into .int files by AIMALL."""

    from ichor.globals import GLOBALS

    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript(SCRIPT_NAMES["aimall"])  # SCRIPT_NAMES["aimall"] gives a path to the AIMALL.sh script
    for point in points:
        if not point.wfn.path.with_suffix(".aim").exists():
            if GLOBALS.METHOD in constants.AIMALL_FUNCTIONALS:
                point.wfn.check_header()
            submission_script.add_command(AIMAllCommand(point.wfn.path))
    submission_script.write()
    return submission_script.submit()


def check_aimall_output(wfn_file: str):
    # AIMAll deletes this sh file when it has successfully completed
    # If this file still exists then something went wrong
    logger.debug(f"Checking {wfn_file}")
    if not Path(wfn_file).with_suffix(".sh").exists():
        logger.debug(f"AIMAll finished")
        print_completed()
    else:
        logger.error(f"AIMAll Job {wfn_file} failed to run")
