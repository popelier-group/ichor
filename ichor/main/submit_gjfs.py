from pathlib import Path

from ichor.logging import logger
from ichor.points import PointsDirectory
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, print_completed)


def submit_gjfs(directory: Path):
    """Function that submits all .gjf files in a directory to Gaussian, which will output .wfn files.

    :param directory: A Path object which is the path of the directory (commonly traning set path, sample pool path, etc.).
    """
    # matt_todo: Maybe add the Path from which gjfs are being submitted in the logger
    logger.info("Submitting gjfs to Gaussian")
    points = PointsDirectory(directory)  # a directory which contains points (a bunch of molecular geometries)
    # make a SubmissionScript instance which is going to house all the jobs that are going to be ran
    submission_script = SubmissionScript(SCRIPT_NAMES["gaussian"])  # SCRIPT_NAMES["gaussian"] gives a path to the GAUSSIAN.sh script
    for point in points:  # point is an instance of PointDirectory
        # point.gjf.read()  # <- Shouldn't be needed
        point.gjf.write()
        submission_script.add_command(GaussianCommand(point.gjf.path))  # make a list of GaussianCommand instances.
    # write the final submission script file that containing the job that needs to be ran (could be an array job that has many tasks)
    submission_script.write()
    # submit the final submission script to the queuing system, so that job is ran on compute nodes.
    submission_script.submit()


def check_gaussian_output(gaussian_file: str):
    """ Checks if Gaussian jobs ran correctly and a full .wfn file is returned. If there is no .wfn file or it does not
    have the correct contents, then rerun Gaussian."""
    # matt_todo: Check here that the .wfn file has the Normal termination line to prevent having .wfn outputs with errors
    if Path(gaussian_file).with_suffix(".wfn").exists():
        print_completed()
    else:
        logger.error(f"Gaussian Job {gaussian_file} failed to run")
