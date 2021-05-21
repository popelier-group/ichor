from pathlib import Path
from typing import Optional

from ichor import constants
from ichor.batch_system import JobID
from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script.aimall import AIMAllCommand
from ichor.submission_script.submision_script import SubmissionScript


def submit_wfns(directory: Path) -> Optional[JobID]:
    from ichor.globals import GLOBALS

    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript("AIMSub.sh")
    for point in points:
        if GLOBALS.METHOD in constants.AIMALL_FUNCTIONALS:
            point.wfn.check_header()
        submission_script.add_command(AIMAllCommand(point.wfn.path))
    submission_script.write()
    return submission_script.submit()
