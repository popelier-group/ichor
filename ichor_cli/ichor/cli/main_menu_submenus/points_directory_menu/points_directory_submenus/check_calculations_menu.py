"""Menus which check that the Gaussian and AIMAll calculations of a PointsDirectory have
finished, i.e. that there is a wavefunction for every geometry and a set of atomic files
for every wavefunction, and which submit the points that are not finished again.

Both menus are the same apart from which calculation they check, so they share their
options and the functions which run a check, report its outcome and resubmit the points
it found. The settings a resubmission is made with are the ones of the menu the points
were submitted from in the first place (the Submit Gaussian Menu and the Submit AIMAll
Menu), so that points which are calculated again are calculated the same way as the rest
of the set.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Type, Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.points_directory_menu.points_directory_submenus.submit_aimall_menu import (  # noqa: E501
    submit_aimall_menu_options,
)
from ichor.cli.main_menu_submenus.points_directory_menu.points_directory_submenus.submit_gaussian_menu import (  # noqa: E501
    submit_gaussian_menu_options,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary,
    print_summary_and_pause,
    user_input_bool,
    user_input_free_flow,
    user_input_path,
)
from ichor.core.files import PointDirectory, PointsDirectory, PointsDirectoryParent
from ichor.core.processing import (
    AimallCheck,
    GaussianCheck,
    PointsDirectoryCheck,
    wfn_is_finished,
)
from ichor.hpc.main import (
    submit_points_directory_to_aimall,
    submit_points_directory_to_gaussian,
)
from ichor.hpc.submission_commands import GaussianCommand

CHECK_GAUSSIAN_MENU_DESCRIPTION = MenuDescription(
    "Check Gaussian Menu",
    subtitle="Use this menu to check that Gaussian has written a wavefunction for "
    "every point, and to resubmit the points which are not finished.\n",
)

CHECK_AIMALL_MENU_DESCRIPTION = MenuDescription(
    "Check AIMAll Menu",
    subtitle="Use this menu to check that AIMAll has written the atomic files for "
    "every point, and to resubmit the points which are not finished.\n",
)

CHECK_GAUSSIAN_MENU_DEFAULTS = {
    "default_check_file_contents": True,
    "default_write_report": True,
    "default_report_name": "GAUSSIAN-CHECK-REPORT.txt",
}

CHECK_AIMALL_MENU_DEFAULTS = {
    "default_check_file_contents": True,
    "default_write_report": True,
    "default_report_name": "AIMALL-CHECK-REPORT.txt",
}

# a check of a large PointsDirectory can find thousands of unfinished points, which are
# all written to the report file but would scroll the menu away if they were all printed
MAX_PROBLEMS_PRINTED = 20


# dataclass used to store values for both check menus
@dataclass
class CheckCalculationMenuOptions(MenuOptions):

    selected_check_file_contents: bool
    selected_write_report: bool
    selected_report_name: str

    # defaults to the current working directory
    selected_points_directory_path: Path = field(default_factory=lambda: Path.cwd())

    def check_path(self):

        pd_path = Path(self.selected_points_directory_path)
        if not pd_path.is_dir():
            return "Current path is not a directory."

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (pd_path.suffix != PointsDirectory._suffix) and (
            pd_path.suffix != PointsDirectoryParent._suffix
        ):
            return f"Current path: {pd_path} might not be PointsDirectory-like)."


# initialize dataclasses for storing information for the menus
check_gaussian_menu_options = CheckCalculationMenuOptions(
    *CHECK_GAUSSIAN_MENU_DEFAULTS.values()
)

check_aimall_menu_options = CheckCalculationMenuOptions(
    *CHECK_AIMALL_MENU_DEFAULTS.values()
)


def select_points_directory(menu_options: CheckCalculationMenuOptions):
    """Asks user to update points directory and then updates the given menu options."""
    pd_path = user_input_path("Change PointsDirectory Path: ")
    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
        pd_path
    ).absolute()
    menu_options.selected_points_directory_path = (
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
    )


def shorten_names(names: Sequence[str]) -> str:
    """Formats a list of point names for printing, cutting it short if it is long."""

    names = list(names)
    if len(names) > MAX_PROBLEMS_PRINTED:
        return (
            ", ".join(names[:MAX_PROBLEMS_PRINTED])
            + f" (and {len(names) - MAX_PROBLEMS_PRINTED} more)"
        )

    return ", ".join(names)


def has_geometry(point: PointDirectory) -> bool:
    """Whether a point has a geometry Gaussian can be given, i.e. an .xyz file to write
    a .gjf from or a .gjf file which is already there."""
    return bool(point.xyz) or bool(point.gjf)


def has_usable_wfn(point: PointDirectory) -> bool:
    """Whether a point has a wavefunction AIMAll can be given, i.e. one which Gaussian
    finished writing. A wavefunction which was cut short is of no use to AIMAll, and
    reading it (as submitting it would) fails, so such a point is left for Gaussian to
    calculate again first."""

    # the wfn attribute is a list if a point somehow holds more than one wfn file
    wfns = point.wfn if isinstance(point.wfn, list) else [point.wfn]

    return any(wfn and wfn_is_finished(wfn.path) for wfn in wfns)


def make_check(
    check_class: Type[PointsDirectoryCheck],
    menu_options: CheckCalculationMenuOptions,
) -> Optional[PointsDirectoryCheck]:
    """Checks the selected PointsDirectory (or parent to many PointsDirectory-ies) for
    the output of one of the calculations.

    The check is done here rather than being submitted to a compute node, as it only
    looks at which files are on disk (and, if asked to, at the last line of each of
    them), so even a PointsDirectory of many thousands of points is checked in seconds.

    :param check_class: The check to run, e.g. ``GaussianCheck`` or ``AimallCheck``.
    :param menu_options: The options of the menu the check is run from.
    :return: The finished check, or None if the selected path could not be read as a
        PointsDirectory (in which case that has been shown to the user).
    """

    points_directory_path = (
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
    )

    print(f"CHECKING {points_directory_path}\n")

    try:
        return check_class(
            points_directory_path,
            check_file_contents=menu_options.selected_check_file_contents,
        )
    # the path is only checked for being PointsDirectory-like when it is selected, so it
    # can still be a directory which does not exist or holds no points at all
    except FileNotFoundError as e:
        print_summary_and_pause(
            f"{check_class.calculation_name} CHECK NOT RUN",
            {"PointsDirectory": points_directory_path, "Problem": e},
            [
                "The selected path could not be read as a PointsDirectory, so there is "
                "nothing to check. Select the directory which holds the point "
                "directories (or, for many PointsDirectory-ies at once, the parent "
                "directory holding them) and try again."
            ],
        )
        return None


def print_problem_points(check: PointsDirectoryCheck):
    """Prints the points which are not finished, with what is wrong with each of them.

    Only the points which need looking at are printed, as a finished PointsDirectory
    would otherwise scroll thousands of OK lines past the user.
    """

    problem_points = check.problem_points
    if not problem_points:
        return

    print(f"{len(problem_points)} of {check.npoints} points are not finished:\n")
    for result in problem_points[:MAX_PROBLEMS_PRINTED]:
        print(
            f"  {check.display_name(result)}: {result.status}, "
            f"{'; '.join(result.problems)}"
        )
    if len(problem_points) > MAX_PROBLEMS_PRINTED:
        print(
            f"  ... and {len(problem_points) - MAX_PROBLEMS_PRINTED} more "
            "(see the report file for all of them)"
        )
    print()


def run_check(
    check_class: Type[PointsDirectoryCheck],
    menu_options: CheckCalculationMenuOptions,
    notes: List[str],
):
    """Checks the selected PointsDirectory, prints the points which are not finished and
    optionally writes a report containing every point.

    :param check_class: The check to run, e.g. ``GaussianCheck`` or ``AimallCheck``.
    :param menu_options: The options of the menu the check is run from.
    :param notes: Sentences printed underneath the summary, explaining what the outcome
        of this particular check means and what to do about it.
    """

    check = make_check(check_class, menu_options)
    if check is None:
        return

    print_problem_points(check)

    report_path = "not written"
    if menu_options.selected_write_report:
        report_path = check.write_report(
            Path(check.path) / menu_options.selected_report_name
        )

    counts = check.counts
    ichor.hpc.global_variables.LOGGER.info(
        f"{check_class.calculation_name} check of {check.path}: "
        f"{counts['OK']}/{check.npoints} points finished."
    )

    print_summary_and_pause(
        f"{check_class.calculation_name} CHECK FINISHED",
        {
            "PointsDirectory": check.path,
            "Points checked": f"{check.npoints:,}",
            "Finished": f"{counts['OK']:,}",
            "Missing output": f"{counts['MISSING']:,}",
            "Incomplete output": f"{counts['INCOMPLETE']:,}",
            "Checked file contents": menu_options.selected_check_file_contents,
            "Report": report_path,
        },
        notes,
    )


def problem_points_by_points_directory(
    check: PointsDirectoryCheck,
    can_be_resubmitted: Callable[[PointDirectory], bool],
) -> Tuple[Dict[Path, List[PointDirectory]], List[str]]:
    """Collects the points a check found problems with, so that they can be calculated
    again.

    The points are grouped by the PointsDirectory they are in, because each
    PointsDirectory is submitted as its own job array (and writes its outputs and errors
    into its own directory), just as it is when the whole set is submitted.

    :param check: The finished check whose problem points are to be resubmitted.
    :param can_be_resubmitted: Decides whether a point has what the calculation needs to
        run at all, e.g. a geometry for Gaussian or a wavefunction for AIMAll.
    :return: The points to resubmit, keyed by the path of the PointsDirectory they are
        in, and the names of the points which cannot be resubmitted.
    """

    points_by_points_directory = {}
    skipped_points = []

    for result in check.problem_points:
        point = PointDirectory(result.path)
        if not can_be_resubmitted(point):
            skipped_points.append(check.display_name(result))
            continue
        # a point directory is inside the PointsDirectory which holds it
        points_by_points_directory.setdefault(result.path.parent, []).append(point)

    return points_by_points_directory, skipped_points


def confirm_resubmission(
    check: PointsDirectoryCheck,
    points_by_points_directory: Dict[Path, List[PointDirectory]],
    skipped_points: List[str],
    skipped_reason: str,
    settings: dict,
    settings_menu: str,
) -> bool:
    """Shows which points would be calculated again, and with which settings, and asks
    whether to go ahead with submitting them.

    :param check: The finished check whose problem points are to be resubmitted.
    :param points_by_points_directory: The points to resubmit, as collected by
        :func:`problem_points_by_points_directory`.
    :param skipped_points: The names of the points which cannot be resubmitted.
    :param skipped_reason: Why those points cannot be resubmitted.
    :param settings: The settings the calculation would be submitted with.
    :param settings_menu: The name of the menu those settings come from.
    :return: True if there is something to resubmit and the user asked for it to be
        submitted. False otherwise, in which case the reason has been shown.
    """

    npoints = sum(len(points) for points in points_by_points_directory.values())

    if not npoints:

        if skipped_points:
            notes = [
                f"None of the {len(skipped_points)} unfinished points can be "
                f"resubmitted, as {skipped_reason}.",
                f"The points in question are: {shorten_names(skipped_points)}.",
            ]
        else:
            notes = [
                "Every point has the output of this calculation, so there is nothing "
                "to submit again."
            ]

        print_summary_and_pause(
            f"NOTHING TO RESUBMIT TO {check.calculation_name}",
            {
                "PointsDirectory": check.path,
                "Points checked": f"{check.npoints:,}",
                "Unfinished": f"{len(check.problem_points):,}",
            },
            notes,
        )
        return False

    notes = [
        f"The settings above are the ones of the {settings_menu}, which is where they "
        "are changed. Points which are calculated again should be calculated the same "
        "way as the rest of the set, so make sure they are the settings this set was "
        "made with.",
        "The points are submitted as a job array, one job array per PointsDirectory, "
        "and the output of the unfinished points is overwritten as they are calculated "
        "again.",
    ]

    if skipped_points:
        notes.append(
            f"{len(skipped_points)} of the unfinished points are left out, as "
            f"{skipped_reason}: {shorten_names(skipped_points)}."
        )

    print_summary(
        f"POINTS TO RESUBMIT TO {check.calculation_name}",
        {
            "PointsDirectory": check.path,
            "Points checked": f"{check.npoints:,}",
            "To resubmit": f"{npoints:,}",
            "Left out": f"{len(skipped_points):,}",
            "Job arrays": f"{len(points_by_points_directory)}",
            **settings,
        },
        notes,
    )

    return user_input_bool(
        f"Resubmit {npoints} point{'s' if npoints != 1 else ''} (yes/no): ", False
    )


# class with static methods for each menu item that calls a function.
class CheckGaussianFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates the menu options."""
        select_points_directory(check_gaussian_menu_options)

    @staticmethod
    def select_check_file_contents():
        """Asks user whether the wavefunctions which are there should also be checked
        for having been written to the end."""
        check_gaussian_menu_options.selected_check_file_contents = user_input_bool(
            "Check contents of wfn files (yes/no): ",
            check_gaussian_menu_options.selected_check_file_contents,
        )

    @staticmethod
    def select_write_report():
        """Asks user whether a report file should be written."""
        check_gaussian_menu_options.selected_write_report = user_input_bool(
            "Write report file (yes/no): ",
            check_gaussian_menu_options.selected_write_report,
        )

    @staticmethod
    def select_report_name():
        """Asks user for the name of the report file, which is written into the selected
        PointsDirectory."""
        check_gaussian_menu_options.selected_report_name = user_input_free_flow(
            "Enter report file name: ",
            check_gaussian_menu_options.selected_report_name,
        )

    @staticmethod
    def check_gaussian_wfns():
        """Checks that Gaussian has written a wavefunction for every point."""

        run_check(
            GaussianCheck,
            check_gaussian_menu_options,
            [
                "A point with missing output has no wfn file, so Gaussian either has "
                "not run on it yet or crashed before writing anything; a point with "
                "incomplete output has a wfn file which was not written to the end, "
                "which usually means the job ran out of time or was killed.",
                "Points which are not finished are printed above with what is wrong "
                "with them, and the report file lists every point that was checked.",
                "Use the resubmit option of this menu to calculate the unfinished "
                "points again. They are submitted with the settings of the Submit "
                "Gaussian Menu, and only the unfinished points are calculated, so the "
                "points which are already done are not touched.",
            ],
        )

    @staticmethod
    def resubmit_gaussian_points():
        """Checks the selected PointsDirectory and submits the points which are not
        finished back to Gaussian."""

        check = make_check(GaussianCheck, check_gaussian_menu_options)
        if check is None:
            return

        print_problem_points(check)

        # a gjf file is written from the geometry of the point, so a point which has
        # neither a geometry nor an input file has nothing that can be calculated
        points_by_points_directory, skipped_points = problem_points_by_points_directory(
            check, has_geometry
        )

        (method, basis_set, ncores, overwrite_existing_gjfs) = (
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_basis_set,
            submit_gaussian_menu_options.selected_number_of_cores,
            submit_gaussian_menu_options.selected_overwrite_existing_gjfs,
        )

        # add memory link0 to GJF, as the Submit Gaussian Menu does
        mem = (GaussianCommand.memory_per_core - 1) * ncores
        link0 = [f"NProcShared={ncores}", f"Mem={mem}GB"]

        settings = {
            "Method": method,
            "Basis set": basis_set,
            "CPU cores per point": ncores,
            "Memory per point": f"{mem} GB",
            "Overwrite existing gjfs": overwrite_existing_gjfs,
        }

        if not confirm_resubmission(
            check,
            points_by_points_directory,
            skipped_points,
            "they have no .xyz and no .gjf file, so there is no geometry to calculate",
            settings,
            "Submit Gaussian Menu",
        ):
            return

        print("\nSTARTING GAUSSIAN JOB SUBMISSION\n")

        outputs_directory = ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        errors_directory = ichor.hpc.global_variables.FILE_STRUCTURE["errors"]

        job_ids = []
        for points_directory_path, points in points_by_points_directory.items():

            job_ids.append(
                submit_points_directory_to_gaussian(
                    points_directory=points,
                    overwrite_existing=overwrite_existing_gjfs,
                    # the points being resubmitted are exactly the ones whose wfn is
                    # missing or unusable, so nothing is to be skipped here
                    force_calculate_wfn=True,
                    ncores=ncores,
                    method=method,
                    basis_set=basis_set,
                    link0=link0,
                    outputs_dir_path=outputs_directory
                    / points_directory_path.name
                    / "GAUSSIAN",
                    errors_dir_path=errors_directory
                    / points_directory_path.name
                    / "GAUSSIAN",
                )
            )

        npoints = sum(len(points) for points in points_by_points_directory.values())
        ichor.hpc.global_variables.LOGGER.info(
            f"Resubmitted {npoints} unfinished points of {check.path} to Gaussian."
        )

        print_summary_and_pause(
            "UNFINISHED GAUSSIAN POINTS RESUBMITTED",
            {
                "PointsDirectory": check.path,
                "Geometries": f"{npoints:,}",
                "Job arrays": f"{len(points_by_points_directory)}",
                "Job IDs": ", ".join(
                    job_id.id if job_id else "not available" for job_id in job_ids
                ),
                **settings,
            },
            [
                "Only the points which were not finished have been submitted, so the "
                "wavefunctions which are already there are left alone. The wfn file of "
                "a point which was cut short is overwritten when its job runs.",
                "The jobs are queued, so they will not start immediately and this menu "
                "does not wait for them. Check on them with your batch system's queue "
                "command (e.g. qstat / squeue), then run the check again to see whether "
                "they finished this time.",
            ],
        )


class CheckAIMAllFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates the menu options."""
        select_points_directory(check_aimall_menu_options)

    @staticmethod
    def select_check_file_contents():
        """Asks user whether the .int files which are there should also be checked for
        having been written to the end."""
        check_aimall_menu_options.selected_check_file_contents = user_input_bool(
            "Check contents of int files (yes/no): ",
            check_aimall_menu_options.selected_check_file_contents,
        )

    @staticmethod
    def select_write_report():
        """Asks user whether a report file should be written."""
        check_aimall_menu_options.selected_write_report = user_input_bool(
            "Write report file (yes/no): ",
            check_aimall_menu_options.selected_write_report,
        )

    @staticmethod
    def select_report_name():
        """Asks user for the name of the report file, which is written into the selected
        PointsDirectory."""
        check_aimall_menu_options.selected_report_name = user_input_free_flow(
            "Enter report file name: ",
            check_aimall_menu_options.selected_report_name,
        )

    @staticmethod
    def check_aimall_atomicfiles():
        """Checks that AIMAll has written the atomic files for every point."""

        run_check(
            AimallCheck,
            check_aimall_menu_options,
            [
                "AIMAll writes one .int file per atom into a <point>_atomicfiles "
                "directory next to the wavefunction. A point with missing output has no "
                "such directory, so AIMAll has not run on it; a point with incomplete "
                "output is missing the .int file of one or more atoms, or has files "
                "which AIMAll leaves behind when it crashes (a .sh script or "
                "intermediate .mog files).",
                "Points which are not finished are printed above with what is wrong "
                "with them, and the report file lists every point that was checked.",
                "Points without a wavefunction cannot be run through AIMAll at all, so "
                "check Gaussian first if many points are missing their atomic files. "
                "Otherwise, use the resubmit option of this menu to calculate the "
                "unfinished points again with the settings of the Submit AIMAll Menu.",
            ],
        )

    @staticmethod
    def resubmit_aimall_points():
        """Checks the selected PointsDirectory and submits the points which are not
        finished back to AIMAll."""

        check = make_check(AimallCheck, check_aimall_menu_options)
        if check is None:
            return

        print_problem_points(check)

        # AIMAll partitions a wavefunction, so a point without a usable one has nothing
        # to run on
        points_by_points_directory, skipped_points = problem_points_by_points_directory(
            check, has_usable_wfn
        )

        method, ncores, naat, encomp = (
            submit_aimall_menu_options.selected_method,
            submit_aimall_menu_options.selected_number_of_cores,
            submit_aimall_menu_options.selected_naat,
            submit_aimall_menu_options.selected_encomp,
        )

        settings = {
            "Method": method,
            "naat setting": naat,
            "encomp setting": encomp,
            "CPU cores per point": ncores,
        }

        if not confirm_resubmission(
            check,
            points_by_points_directory,
            skipped_points,
            "Gaussian has not finished writing their wavefunction, so calculate them "
            "with the Check Gaussian Menu first",
            settings,
            "Submit AIMAll Menu",
        ):
            return

        print("\nSTARTING AIMALL JOB SUBMISSION\n")

        outputs_directory = ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
        errors_directory = ichor.hpc.global_variables.FILE_STRUCTURE["errors"]

        job_ids = []
        for points_directory_path, points in points_by_points_directory.items():

            job_ids.append(
                submit_points_directory_to_aimall(
                    points_directory=points,
                    method=method,
                    ncores=ncores,
                    naat=naat,
                    encomp=encomp,
                    # the points being resubmitted are exactly the ones whose atomic
                    # files are missing or incomplete, so nothing is to be skipped here
                    force_calculate_ints=True,
                    outputs_dir_path=outputs_directory
                    / points_directory_path.name
                    / "AIMALL",
                    errors_dir_path=errors_directory
                    / points_directory_path.name
                    / "AIMALL",
                )
            )

        npoints = sum(len(points) for points in points_by_points_directory.values())
        ichor.hpc.global_variables.LOGGER.info(
            f"Resubmitted {npoints} unfinished points of {check.path} to AIMAll."
        )

        print_summary_and_pause(
            "UNFINISHED AIMALL POINTS RESUBMITTED",
            {
                "PointsDirectory": check.path,
                "Wavefunctions": f"{npoints:,}",
                "Job arrays": f"{len(points_by_points_directory)}",
                "Job IDs": ", ".join(
                    job_id.id if job_id else "not available" for job_id in job_ids
                ),
                **settings,
            },
            [
                "Only the points which were not finished have been submitted, so the "
                "atomic files which are already there are left alone. The atomicfiles "
                "directory of a point which was cut short is filled in again when its "
                "job runs.",
                "The jobs are queued, so they will not start immediately and this menu "
                "does not wait for them. Check on them with your batch system's queue "
                "command (e.g. qstat / squeue), then run the check again to see whether "
                "they finished this time.",
            ],
        )


# make menu items
check_gaussian_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        CheckGaussianFunctions.select_points_directory,
    ),
    FunctionItem(
        "Check contents of wfn files as well",
        CheckGaussianFunctions.select_check_file_contents,
    ),
    FunctionItem(
        "Write report to file",
        CheckGaussianFunctions.select_write_report,
    ),
    FunctionItem(
        "Change report file name",
        CheckGaussianFunctions.select_report_name,
    ),
    FunctionItem(
        "Check Gaussian wavefunctions",
        CheckGaussianFunctions.check_gaussian_wfns,
    ),
    FunctionItem(
        "Resubmit unfinished points to Gaussian",
        CheckGaussianFunctions.resubmit_gaussian_points,
    ),
]

check_aimall_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        CheckAIMAllFunctions.select_points_directory,
    ),
    FunctionItem(
        "Check contents of int files as well",
        CheckAIMAllFunctions.select_check_file_contents,
    ),
    FunctionItem(
        "Write report to file",
        CheckAIMAllFunctions.select_write_report,
    ),
    FunctionItem(
        "Change report file name",
        CheckAIMAllFunctions.select_report_name,
    ),
    FunctionItem(
        "Check AIMAll atomic files",
        CheckAIMAllFunctions.check_aimall_atomicfiles,
    ),
    FunctionItem(
        "Resubmit unfinished points to AIMAll",
        CheckAIMAllFunctions.resubmit_aimall_points,
    ),
]

# initialize menus
check_gaussian_menu = ConsoleMenu(
    this_menu_options=check_gaussian_menu_options,
    title=CHECK_GAUSSIAN_MENU_DESCRIPTION.title,
    subtitle=CHECK_GAUSSIAN_MENU_DESCRIPTION.subtitle,
    prologue_text=CHECK_GAUSSIAN_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=CHECK_GAUSSIAN_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=CHECK_GAUSSIAN_MENU_DESCRIPTION.show_exit_option,
)

check_aimall_menu = ConsoleMenu(
    this_menu_options=check_aimall_menu_options,
    title=CHECK_AIMALL_MENU_DESCRIPTION.title,
    subtitle=CHECK_AIMALL_MENU_DESCRIPTION.subtitle,
    prologue_text=CHECK_AIMALL_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=CHECK_AIMALL_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=CHECK_AIMALL_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(check_gaussian_menu, check_gaussian_menu_items)
add_items_to_menu(check_aimall_menu, check_aimall_menu_items)
