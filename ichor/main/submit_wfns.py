import sys
from pathlib import Path
from typing import List, Optional

from ichor import constants
from ichor.batch_system import JobID
from ichor.files import PointsDirectory
from ichor.logging import logger
from ichor.submission_script import (SCRIPT_NAMES, AIMAllCommand,
                                     SubmissionScript, print_completed)


def submit_wfns(
    directory: Path, atoms: Optional[List[str]] = None
) -> Optional[JobID]:
    """Submits .wfn files which will be partitioned into .int files by AIMALL. Each topological atom i the system has its own .int file"""
    from ichor.globals import GLOBALS

    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript(
        SCRIPT_NAMES["aimall"]
    )  # SCRIPT_NAMES["aimall"] gives a path to the AIMALL.sh script
    for point in points:
        if (
            not point.wfn.path.with_suffix(".aim").exists()
            or point.wfn.path.with_suffix(".sh").exists()
        ):
            if GLOBALS.METHOD in constants.AIMALL_FUNCTIONALS:
                point.wfn.check_header()
            submission_script.add_command(
                AIMAllCommand(point.wfn.path, atoms=atoms)
            )
    logger.info(
        f"Submitting {len(submission_script.commands)} WFN(s) to AIMAll"
    )
    submission_script.write()
    return submission_script.submit()


def check_aimall_output(wfn_file: str):
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
