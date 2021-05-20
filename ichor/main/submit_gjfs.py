from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script.gaussian import GaussianCommand
from ichor.submission_script.submision_script import SubmissionScript


def submit_gjfs(directory):
    logger.info("Submitting gjfs to Gaussian")
    points = PointsDirectory(directory)
    submission_script = SubmissionScript("GaussSub.sh")
    for point in points:
        submission_script.add_command(GaussianCommand(point.gjf.path))
    submission_script.write()
    submission_script.submit()
