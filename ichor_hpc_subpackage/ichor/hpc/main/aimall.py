import sys
from pathlib import Path
from typing import List, Optional

from ichor.core.common.io import remove
from ichor.core.files import AIM, INT, PointsDirectory, FileContents
from ichor.hpc.batch_system import JobID
from ichor.hpc.log import logger
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    AIMAllCommand,
    SubmissionScript,
    print_completed,
)
from typing import Union
from ichor.core.common.constants import AIMALL_FUNCTIONALS


def submit_points_directory_to_aimall(
    points_directory: Union[PointsDirectory, Path], method = "B3LYP", aimall_atoms: Optional[List[str]] = None, force: bool = False) -> Optional[JobID]:
    """Submits .wfn files which will be partitioned into .int files by AIMALL. Each topological atom i the system has its own .int file"""

    method = method.upper()

    logger.info("Submitting wfns to AIMAll")
    if not isinstance(points_directory, PointsDirectory):
        points = PointsDirectory(points_directory)
    list_of_wfn_paths = check_method_in_wfns(points, method)
    return submit_wfns(list_of_wfn_paths, aimall_atoms, force=force)


def check_method_in_wfns(points: PointsDirectory, method) -> List[Path]:
    """ AIMALL needs to know the method from the wfn file. The method needs to be added in the wfn file, otherwise AIMALL gets the method wrong and
    gives the wrong results."""
    
    wfns = []
    for point in points:
        # write out the wfn file with the method modified as needed
        if point.wfn.exists():
            if point.wfn.method != method:
                point.wfn.method = method
                point.wfn.write()
            wfns.append(point.wfn.path)
    return wfns

def submit_wfns(
    wfns: List[Path],
    aimall_atoms: Optional[List[str]] = None,
    force: bool = False,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """ Write out submission script and submit wavefunctions to AIMALL on a cluster.
    
    :param wfns: a list of wavefunction paths which to write to the submission script
    :param atoms: a list of stings corresponding to atom names. These will be the atoms for which AIMALL computes properties.
    :param force: Whether or not to compute AIMALL for this wfn. If force is True, AIMALL will be ran again
    :param hold: An optional JobID to hold for. The AIMALL job will not run until that other job is finished.
    
    """
    with SubmissionScript(SCRIPT_NAMES["aimall"]) as submission_script:
        
        for wfn in wfns:
            if force or not aimall_completed(wfn):
                submission_script.add_command(AIMAllCommand(wfn, atoms=aimall_atoms))
                logger.debug(f"Adding {wfn} to {submission_script.path}")

    if len(submission_script.commands) > 0:
        # todo this will get executed when running from a compute node, but this does not submit any wfns to aimall, it is just used to make the datafile.
        logger.info(
            f"Submitting {len(submission_script.commands)} WFN(s) to AIMAll"
        )
        return submission_script.submit(hold=hold)


def aimall_completed(wfn: Path) -> bool:
    """ This function is used when checking if AIMALL ran successfully. The .aim file as well as if the .int files contain the required information."""
    aim_file = wfn.with_suffix(AIM.filetype)
    if not aim_file.exists():
        return False
    aim = AIM(aim_file)
    for atom, aimdata in aim.items():
        if not aimdata.outfile.exists():
            logger.error(f"AIMAll for {wfn} failed to run for atom '{atom}'")
            return False
        else:
            int_file = INT(aimdata.outfile)
            try:
                assert int_file.integration_error is not FileContents
                assert int_file.q44s is not FileContents
                assert int_file.iqa is not FileContents
            except AttributeError:
                logger.error(
                    f"AIMAll for '{wfn}' failed to run producing invalid int file '{int_file.path}'"
                )
                return False
    return True

def cleanup_failed_aimall(wfn: Path):
    """ Removes atomicfiles directories in a given directory where the wfn is.
    
    :param wfn: A path to a wfn file. The _atomicfiles directory is in the same directory as the .wfn
    """
    atomicfiles = wfn.with_suffix("_atomicfiles")
    if atomicfiles.exists():
        remove(atomicfiles)
        logger.error(
            f"AIMAll for '{wfn}' failed, removing atomicfiles directory '{atomicfiles}'"
        )


def rerun_aimall(wfn_file: str):
    if not wfn_file:
        print_completed()
        sys.exit()
    # AIMAll deletes this sh file when it has successfully completed
    # If this file still exists then something went wrong
    wfn_file = Path(wfn_file)
    aim_file = wfn_file.with_suffix(AIM.filetype)

    if aim_file.exists() and not aimall_completed(wfn_file):
        cleanup_failed_aimall(wfn_file)
    else:
        print_completed()


def scrub_aimall(wfn_file: str):
    """Used by `CheckManager`. Checks if AIMALL job ran correctly. If it did not, it will move the Point to the `FILE_STRUCTURE["aimall_scrubbed_points"]`
    directory and record that it has moved the point in the log file. If a .sh file exists and the integration error for the point is lower than the
    GLOBALS-specified threshold, then this checking function will not do anything.

    :param wfn_file: A string that is a Path to a .wfn file
    """

    from pathlib import Path

    from ichor.core.common.io import last_line
    from ichor.core.files.aim import AIM
    from ichor.core.files.point_directory import PointDirectory
    from ichor.hpc import GLOBALS
    from ichor.hpc.log import logger

    wfn_file = Path(wfn_file)
    point = PointDirectory(wfn_file.parent)
    aim_file = wfn_file.with_suffix(".aim")

    reason: Optional[str] = None
    if not wfn_file.exists():
        reason = f"{wfn_file} does not exist"
    elif "TOTAL ENERGY" not in last_line(wfn_file):
        reason = f"Incomplete WFN ('{wfn_file}') file found"
    elif not point.wfn.exists():
        reason = f"No WFN file found in directory {point.path}"
    elif wfn_file.with_suffix(".sh").exists() or (
        not aim_file.exists()
        and "AIMQB Job Completed" not in last_line(aim_file)
    ):
        reason = f"AIMAll in '{point.path}' did not exit successfully"

    if reason is None:
        aim = AIM(aim_file)
        if not aim.license_check_succeeded:
            logger.warning(
                f"AIMALL Professional License was not used for this calculation ('{aim_file}')"
            )
        if not point.ints:
            reason = f"{INT.filetype} files for '{point.path}' do not exist."
        elif set(aim.keys()) != set(point.ints.keys()):
            reason = f"Atoms in aim file {aim_file} ({set(aim.keys())}) do not correspond to atoms for which int files were made ({set(point.ints.keys())})."

    if reason is None:
        integration_errors = {
            atom: error
            for atom, error in point.ints.integration_error.items()
            if abs(error) > GLOBALS.INTEGRATION_ERROR_THRESHOLD
        }
        if len(integration_errors) > 0:
            reason = (
                "\n".join(
                    f"{point.ints.path} | {atom} | Integration Error: {error}"
                    for atom, error in integration_errors.items()
                )
                + f"\n'{len(integration_errors)}' atom(s) have a greater than integration error threshold ('{GLOBALS.INTEGRATION_ERROR_THRESHOLD}')"
            )

    if reason is not None:
        logger.error(f"'{point.path}' will be ignored | Reason: {reason}")
        point.ignore(reason)

    if reason is not None:
        logger.error(f"'{point.path}' will be ignored | Reason: {reason}")
        point.ignore(reason)
