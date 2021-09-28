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
