from pathlib import Path

from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)


def submit_gjfs(directory: Path):
    """Function that submits all .gjf files in a directory to Gaussian, which will output .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    """
    logger.info("Submitting gjfs to Gaussian")
    points = PointsDirectory(directory)  # a directory which contains points (a bunch of molecular geometries)
    submission_script = SubmissionScript(SCRIPT_NAMES["gaussian"])  # SCRIPT_NAMES["gaussian"] gives a path to the GAUSSIAN.sh script
    for point in points:  # point is an instance of PointDirectory
        # point.gjf.read()  # <- Shouldn't be needed
        point.gjf.write()
        submission_script.add_command(GaussianCommand(point.gjf.path)) # make a list of GaussianCommand instances.
    submission_script.write()
    submission_script.submit()


def check_gaussian_output(gaussian_file: str):
    # matt_todo: Check here that the .wfn file has the Normal termination line o prevent having .wfn outputs with errors
    if Path(gaussian_file).with_suffix(".wfn").exists():
        print_completed()
    else:
        logger.error(f"Gaussian Job {gaussian_file} failed to run")
