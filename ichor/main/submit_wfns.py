from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script.submision_script import SubmissionScript
from ichor.submission_script.aimall import AIMAllCommand
from ichor.globals import GLOBALS
from ichor import constants


def submit_wfns(directory):
    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript("AIMSub.sh")
    for point in points:
        if GLOBALS.METHOD in constants.AIMALL_FUNCTIONALS:
            point.wfn.check_header()
        submission_script.add_command(AIMAllCommand(point.wfn.path))
    submission_script.write()

    from ichor.batch_system import BATCH_SYSTEM
    BATCH_SYSTEM.submit_script(submission_script.path)
