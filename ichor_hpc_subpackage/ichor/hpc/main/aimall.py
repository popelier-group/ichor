import sys
from hashlib import new
from pathlib import Path
from typing import List, Optional

from ichor.core.common.io import remove
from ichor.core.files import AIM, INT, PointsDirectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.log import logger
from ichor.hpc.submission_script import (SCRIPT_NAMES, AIMAllCommand,
                                         SubmissionScript, print_completed)


def submit_points_directory_to_aimall(
    directory: Path, atoms: Optional[List[str]] = None, force: bool = False
) -> Optional[JobID]:
    """Submits .wfn files which will be partitioned into .int files by AIMALL. Each topological atom i the system has its own .int file"""

    logger.info("Submitting wfns to AIMAll")
    points = PointsDirectory(directory)
    wfns = check_wfns(points)
    return submit_wfns(wfns, atoms, force=force)


def check_wfns(points: PointsDirectory) -> List[Path]:
    wfns = []
    for point in points:
        if point.wfn.exists():
            point.wfn.check_header()
            wfns.append(point.wfn.path)
    return wfns


def aimall_completed(wfn: Path) -> bool:
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
                int_file.integration_error
                int_file.q44s
                int_file.iqa
            except AttributeError:
                logger.error(
                    f"AIMAll for '{wfn}' failed to run producing invalid int file '{int_file.path}'"
                )
                return False
    return True


def submit_wfns(
    wfns: List[Path],
    atoms: Optional[List[str]] = None,
    force: bool = False,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    with SubmissionScript(SCRIPT_NAMES["aimall"]) as submission_script:
        for wfn in wfns:
            if force or not aimall_completed(wfn):
                submission_script.add_command(AIMAllCommand(wfn, atoms=atoms))
                logger.debug(f"Adding {wfn} to {submission_script.path}")

    if len(submission_script.commands) > 0:
        # todo this will get executed when running from a compute node, but this does not submit any wfns to aimall, it is just used to make the datafile.
        logger.info(
            f"Submitting {len(submission_script.commands)} WFN(s) to AIMAll"
        )
        return submission_script.submit(hold=hold)


def cleanup_failed_aimall(wfn: Path):
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
    aim_failed = False
    aim_file = wfn_file.with_suffix(AIM.filetype)

    if aim_file.exists():
        aim_failed = not aimall_completed(wfn_file)

    if aim_failed:
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

    from ichor.core.common.io import last_line, mkdir, move
    from ichor.core.files.aim import AIM
    from ichor.core.files.point_directory import PointDirectory
    from ichor.hpc import FILE_STRUCTURE, GLOBALS
    from ichor.hpc.log import logger

    # TODO: check for license and end of aim file, then read aim file with AIM class. Then check if aim file has correct atom info for int files.
    # TODO: then do the integration error check.

    def move_scrubbed_point(point_dir_path: Path):
        """Helper function which takes in a point directory path and moves it to the corresponding scrubbed points directory.

        :return: A Path object to where the point directory was moved to.
        """

        point_dir_name = point_dir_path.name

        mkdir(FILE_STRUCTURE["aimall_scrubbed_points"])
        new_path = FILE_STRUCTURE["aimall_scrubbed_points"] / point_dir_name

        # if a point with the same name already exists in the SCRUBBED_POINTS directory, then add a ~ at the end
        # this can happen for example if aimall fails for two points with the exact same directory name (one from training set, one from validation set or sample pool)
        while new_path.exists():
            point_dir_name = point_dir_name + "~"
            new_path = (
                FILE_STRUCTURE["aimall_scrubbed_points"] / point_dir_name
            )

        # move to new path and record in logger
        move(point_dir_path, new_path)

        return new_path

    wfn_file = Path(wfn_file)
    aim_file = wfn_file.with_suffix(".aim")
    point_dir_path = (
        wfn_file.parent
    )  # returns path to the point directory containing the wfn file

    # if there is a wfn file from Gaussian and the last line contains the TOTAL energy (so Gaussian ran successfully), then check for aimall outputs
    if wfn_file.exists() and ("TOTAL ENERGY" in last_line(wfn_file)):

        # AIMAll deletes this sh file when it has successfully completed
        sh_file = wfn_file.with_suffix(".sh")
        if sh_file.exists():
            new_path = move_scrubbed_point(point_dir_path)
            logger.error(
                f"Moved point directory {point_dir_path} to {new_path} because AIMALL .sh file exists, so AIMALL job did not run successfully."
            )
            # return after point was moved, no need to check the rest
            return

        # if aim file has correct last line, then try to parse .aim file and check corresponding .int files exist
        if "AIMQB Job Completed" in last_line(aim_file):

            try:
                aim_instance = AIM(aim_file)
                if not aim_instance.license_check_succeeded:
                    logger.warning(
                        f"AIMALL Professional License was not used for this calculation {aim_file}."
                    )

                # get the atom names which are in the aim file (eg. {"O1", "H2", "H3"}). Make into a set to be able to compare int files.
                atom_names_in_aim_file = set(list(aim_instance.keys()))
                point = PointDirectory(point_dir_path)
                if point.ints:
                    atom_names_in_ints_dir = set(list(point.ints.keys()))
                    if not atom_names_in_aim_file == atom_names_in_ints_dir:
                        new_path = move_scrubbed_point(point_dir_path)
                        logger.error(
                            f"Atoms in aim file {aim_file} ({atom_names_in_aim_file}) do not correspond "
                            + f"to atoms for which int files were made ({atom_names_in_ints_dir})."
                            + f"Point moved to {new_path}."
                        )
                        # return after point was moved, no need to check the rest
                        return

                # if ints do not exist, then move point because .int file need to exist after AIMALL
                else:
                    new_path = move_scrubbed_point(point_dir_path)
                    logger.error(
                        f".int files for the current point {point_dir_path} do not exist. Point moved to {new_path}."
                    )
                    return

                # find if any atoms have integration error above the threshold set in ichor.hpc.globals
                n_integration_error = 0
                if point.ints:
                    integration_errors = point.integration_error
                    for atom, integration_error in integration_errors.items():
                        if (
                            abs(integration_error)
                            > GLOBALS.INTEGRATION_ERROR_THRESHOLD
                        ):
                            logger.error(
                                f"{point_dir_path} | {atom} | Integration Error: {integration_error}"
                            )
                            n_integration_error += 1
                # if any atoms have larger integration error, scrub the point
                if n_integration_error > 0:
                    new_path = move_scrubbed_point(point_dir_path)
                    logger.error(
                        f"Moved point directory {point_dir_path} to {new_path} because "
                        + f"AIMALL integration error for {n_integration_error} atom(s) was greater than {GLOBALS.INTEGRATION_ERROR_THRESHOLD}."
                    )
                    return

            # TODO: more explicit except that has error type, so that logger information can be better
            # catch if anything does not work in the steps above
            except:
                new_path = move_scrubbed_point(point_dir_path)
                logger.error(
                    f"Moved point directory {point_dir_path} to {new_path} because something failed when parsing .aim or .int files."
                )
                return

        # if AIMALL does not have correct last line, then move point
        else:
            new_path = move_scrubbed_point(point_dir_path)
            logger.error(
                f"Moved point directory {point_dir_path} to {new_path} because {aim_file} did not have correct last line."
            )
            return

    # if a wfn file does not exist for some reason, we do not want this point as well. This shouldn't really be needed as points without wfn
    # files should be cleaned up after running Gaussian. But use this as another check.
    else:
        new_path = move_scrubbed_point(point_dir_path)
        logger.error(
            f"Moved point directory {point_dir_path} to {new_path} because .wfn file does not exist after AIMALL was ran."
        )
        return
