"""Menu which checks that the Gaussian and AIMAll calculations of a PointsDirectory have
finished, i.e. that there is a wavefunction for every geometry and a set of atomic files
for every wavefunction, and which submits the points that are not finished again.

A check prints what is wrong with each unfinished point, followed by a summary naming
them, and then offers to save a report of every point which was checked. A resubmission
runs the same check and queues the points it found, with the settings of the menu they
were submitted from in the first place (the Submit Gaussian Menu and the Submit AIMAll
Menu), so that points which are calculated again are calculated the same way as the rest
of the set. Those settings can be changed for a resubmission if they need to be.

The Gaussian side of the menu also looks for points which are not in the set at all.
The points of a set are named after the geometry they came from, so a point directory
which has been deleted leaves a hole in that sequence, which a check of the point
directories which are there cannot see. Those points can be made again from the
trajectory the set was written out of and submitted to Gaussian along with the ones which
did not finish, so that a set which lost some of its points ends up whole again.
"""

import textwrap
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
    points_directory_selected,
    print_summary,
    print_summary_and_pause,
    user_input_bool,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.cli.useful_functions.summary import SUMMARY_WIDTH
from ichor.core.files import (
    count_geometries_in_xyz,
    PointDirectory,
    PointsDirectory,
    PointsDirectoryParent,
)
from ichor.core.processing import (
    AimallCheck,
    GaussianCheck,
    matching_geometries,
    MissingPointsCheck,
    points_are_centred,
    PointsDirectoryCheck,
    restore_missing_points,
    wfn_is_finished,
)
from ichor.hpc.main import (
    submit_points_directory_to_aimall,
    submit_points_directory_to_gaussian,
)
from ichor.hpc.submission_commands import GaussianCommand
from tqdm import tqdm

CHECK_CALCULATIONS_MENU_DESCRIPTION = MenuDescription(
    "Check Point Calculations Menu",
    subtitle="Use this menu to check that the Gaussian and AIMAll calculations of a "
    "PointsDirectory have finished, and to resubmit the points which have not.\n",
)

# name of the report file, which is written into the directory which was checked
REPORT_NAME = "{}-CHECK-REPORT.txt"

# how many points are printed with what is wrong with them. A check of a large
# PointsDirectory can find thousands of unfinished points, and their problems tend to be
# the same few sentences over and over, so only the first handful are spelled out. The
# summary underneath them names the rest, and the report file has all of them
MAX_PROBLEMS_PRINTED = 10

# how many point names are listed per status in the summary of unfinished points. This is
# higher than the number of points printed with what is wrong with them, as the summary
# is only names and so fits many more of them on the screen
MAX_NAMES_SUMMARISED = 60


# dataclass used to store values for CheckCalculationsMenu
@dataclass
class CheckCalculationsMenuOptions(MenuOptions):

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


# initialize dataclass for storing information for menu
check_calculations_menu_options = CheckCalculationsMenuOptions()


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
) -> Optional[PointsDirectoryCheck]:
    """Checks the selected PointsDirectory (or parent to many PointsDirectory-ies) for
    the output of one of the calculations.

    The check is done here rather than being submitted to a compute node, as it only
    looks at which files are on disk and at the last line of each of them, so even a
    PointsDirectory of many thousands of points is checked in seconds.

    :param check_class: The check to run, e.g. ``GaussianCheck`` or ``AimallCheck``.
    :return: The finished check, or None if there is nothing at the selected path to
        check (in which case that has been shown to the user).
    """

    points_directory_path = (
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
    )

    # without this, a menu whose PointsDirectory was never selected reports that none of
    # the zero points it found are missing anything
    if not points_directory_selected(
        points_directory_path,
        f"check for {check_class.calculation_name} output",
        select_with="Use 'Select PointsDirectory Path or Parent to PointsDirectory' in this menu first.",
    ):
        return None

    print(f"CHECKING {points_directory_path}\n")
    # the point directories are read before the check itself can report any progress,
    # which is a wait of its own for a large set, so say what is going on first
    print("Reading the point directories...\n")

    try:
        return check_class(points_directory_path)
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
    """Prints the points which are not finished: first what is wrong with each of them,
    then a summary listing which points are missing their output and which have
    incomplete output, so that the names can be read off the screen without opening the
    report file.

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
        print(f"  ... and {len(problem_points) - MAX_PROBLEMS_PRINTED} more")
    print()

    names_by_status = {}
    for result in problem_points:
        names_by_status.setdefault(result.status, []).append(check.display_name(result))

    print("Summary of the unfinished points:\n")

    # the counts are keyed in a fixed order, so the statuses are always reported in the
    # same order rather than in the order the points happen to be in
    for status in check.counts:

        names = names_by_status.get(status)
        if not names:
            continue

        listed_names = ", ".join(names[:MAX_NAMES_SUMMARISED])
        if len(names) > MAX_NAMES_SUMMARISED:
            listed_names += f", ... and {len(names) - MAX_NAMES_SUMMARISED} more"

        print(f"  {status} ({len(names)}):")
        for line in textwrap.wrap(listed_names, SUMMARY_WIDTH - 4):
            print(f"    {line}")
        print()


def find_missing_points(
    points_directory_path: Path,
    ngeometries: Optional[int] = None,
    every: int = 1,
) -> Optional[MissingPointsCheck]:
    """Looks for points which are missing from the sequence of the selected set.

    :param points_directory_path: Path of the PointsDirectory (or of a parent to many)
        to look in.
    :param ngeometries: How many geometries the trajectory the set was made from holds,
        defaults to None (i.e. the trajectory is not known, so only the holes between the
        points which are there are found).
    :param every: How many geometries of the trajectory each point steps over, defaults
        to 1.
    :return: The finished check, or None if the path could not be read.
    """

    try:
        return MissingPointsCheck(
            points_directory_path, ngeometries=ngeometries, every=every
        )
    except FileNotFoundError:
        return None


def print_missing_points(check: MissingPointsCheck):
    """Prints the points which are missing from the sequence of the set, i.e. the ones
    which are not there to be checked at all."""

    if not check.nmissing:
        return

    print(f"{check.nmissing} points are missing from the sequence of this set:\n")

    for sequence in check.sequences:

        if not sequence.missing:
            continue

        names = [point.name for point in sequence.missing]
        listed_names = ", ".join(names[:MAX_NAMES_SUMMARISED])
        if len(names) > MAX_NAMES_SUMMARISED:
            listed_names += f", ... and {len(names) - MAX_NAMES_SUMMARISED} more"

        print(
            f"  {sequence.system_name} ({sequence.npresent:,} points there, "
            f"{sequence.nmissing:,} missing):"
        )
        for line in textwrap.wrap(listed_names, SUMMARY_WIDTH - 4):
            print(f"    {line}")
        print()


def matched_trajectory(
    check: MissingPointsCheck, trajectory_path: Path, every: int
) -> Tuple[bool, int]:
    """Checks a trajectory against the points of the set which are still there, and asks
    what to do if it does not look like the trajectory the set was made from.

    The geometry of a point which is missing is taken out of the trajectory by its
    position in it, so a trajectory which is not the one the set was made from would
    quietly fill the holes in the set with the wrong geometries. That is worse than
    leaving the holes in it, so it is ruled out before anything is written.

    :param check: The check which found the missing points.
    :param trajectory_path: Path of the trajectory (.xyz) file.
    :param every: How many geometries of the trajectory each point steps over.
    :return: Whether to go ahead, and the (possibly changed) number of geometries of the
        trajectory each point steps over.
    """

    while True:

        ncompared, nmatched = matching_geometries(
            check.present_point_paths, trajectory_path, every
        )

        if ncompared and nmatched == ncompared:
            print(
                f"\nThe geometries of {nmatched} of the points which are there are the "
                f"geometries this trajectory has at their positions, so it is the "
                "trajectory this set was made from.\n"
            )
            return True, every

        if not ncompared:
            notes = [
                "None of the points which are there could be compared against the "
                "trajectory, either because their geometries could not be read or "
                "because the trajectory has no geometry at their positions.",
                "Going ahead means trusting that this is the trajectory the set was "
                "made from, which cannot be checked here.",
            ]
        else:
            notes = [
                f"Only {nmatched} of the {ncompared} points which were compared hold "
                "the geometry this trajectory has at their position, so this is "
                "probably not the trajectory this set was made from, or geometries "
                "have been taken out of it since the set was made.",
                "If the set was written out in chunks from every nth geometry of the "
                "trajectory, its points are numbered one after the other rather than by "
                "where their geometry is in the trajectory. Choose 'change' to say what "
                "n was, and the points will be lined up against the trajectory again.",
                "Going ahead anyway would fill the holes in the set with whichever "
                "geometries this trajectory has at those positions, which are not the "
                "geometries the points which were deleted had.",
            ]

        print_summary(
            "TRAJECTORY DOES NOT MATCH THE SET",
            {
                "PointsDirectory": check.path,
                "Trajectory": trajectory_path,
                "Points compared": f"{ncompared:,}",
                "Points which match": f"{nmatched:,}",
                "Geometries per point": every,
            },
            notes,
        )

        answer = user_input_restricted(
            ["no", "yes", "change"],
            "Make the missing points from this trajectory anyway "
            "(change to say how many geometries of the trajectory each point steps "
            "over): ",
            "no",
        )

        if answer == "yes":
            return True, every
        if answer == "no":
            return False, every

        every = user_input_int(
            "Enter how many geometries of the trajectory each point steps over: ",
            every,
            minimum=1,
        )


def restore_points_missing_from_sequence(
    points_directory_path: Path,
) -> List[PointDirectory]:
    """Offers to make the points which are missing from the sequence of a set again, out
    of the trajectory the set was written out of.

    The point directories are written exactly as they were written when the set was made
    (a directory named after the point, holding the .xyz file of its geometry), so the
    points which are made again are calculated the same way as the rest of the set when
    they are submitted.

    :param points_directory_path: Path of the PointsDirectory (or of a parent to many).
    :return: The points which were made again, ready to be submitted to Gaussian.
    """

    check = find_missing_points(points_directory_path)
    if check is None:
        return []

    print_missing_points(check)

    if not user_input_bool(
        "Make the points which are missing from the sequence of this set again, from "
        "the trajectory it was made from (yes/no): ",
        bool(check.nmissing),
    ):
        return []

    trajectory_path = Path(
        user_input_path("Enter the path of the trajectory this set was made from: ")
    )
    if not trajectory_path.is_file():
        print_summary_and_pause(
            "TRAJECTORY NOT FOUND",
            {"Trajectory": trajectory_path},
            [
                "There is no file at that path, so there is nothing to make the missing "
                "points from. No point directories have been made."
            ],
        )
        return []

    print("\nReading the trajectory...\n")
    ngeometries = count_geometries_in_xyz(trajectory_path)

    go_ahead, every = matched_trajectory(check, trajectory_path, 1)
    if not go_ahead:
        return []

    # now that the trajectory is known, the points which were deleted from the end of the
    # set can be found as well, which the names of the points on their own cannot show
    check = find_missing_points(
        points_directory_path, ngeometries=ngeometries, every=every
    )
    if check is None or not check.nmissing:
        print_summary_and_pause(
            "NO POINTS MISSING FROM THE SET",
            {
                "PointsDirectory": points_directory_path,
                "Trajectory": trajectory_path,
                "Geometries in the trajectory": f"{ngeometries:,}",
                "Points in the set": f"{check.npresent:,}" if check else "0",
            },
            [
                "The set holds a point for every geometry of the trajectory it was made "
                "from, so there is nothing to make again."
            ],
        )
        return []

    print_missing_points(check)

    # a point which is made again should be made the same way as the rest of the set it
    # is going into, so it is centred only if the points which are there are
    centred = points_are_centred(check.present_point_paths)

    print_summary(
        "POINTS MISSING FROM THE SET",
        {
            "PointsDirectory": points_directory_path,
            "Trajectory": trajectory_path,
            "Geometries in the trajectory": f"{ngeometries:,}",
            "Points in the set": f"{check.npresent:,}",
            "Points missing": f"{check.nmissing:,}",
            "Geometries centred": centred,
        },
        [
            "These points are not in the set at all, so neither the Gaussian check nor "
            "the AIMAll check can see them. Their geometries are still in the "
            "trajectory the set was made from, so the point directories can be written "
            "again and calculated.",
            "The geometries are written the way the ones which are there were written, "
            "so the points which are made again are no different from the rest of the "
            "set. Nothing which is already in the set is touched.",
        ],
    )

    if not user_input_bool(
        f"Make {check.nmissing} point director"
        f"{'ies' if check.nmissing != 1 else 'y'} again (yes/no): ",
        True,
    ):
        return []

    print("\nWriting the point directories...\n")
    restored_paths, not_in_trajectory = restore_missing_points(
        check.missing, trajectory_path, every=every, centre=centred
    )

    ichor.hpc.global_variables.LOGGER.info(
        f"Made {len(restored_paths)} points of {points_directory_path} again from "
        f"{trajectory_path}."
    )

    notes = [
        "The points which were made again hold the geometry they had, and no more, so "
        "they are submitted to Gaussian along with the points which did not finish."
    ]
    if not_in_trajectory:
        notes.append(
            f"{len(not_in_trajectory)} of the missing points could not be made, as the "
            "trajectory has no geometry at their position: "
            f"{shorten_names([point.name for point in not_in_trajectory])}."
        )

    print_summary(
        "MISSING POINTS MADE AGAIN",
        {
            "PointsDirectory": points_directory_path,
            "Trajectory": trajectory_path,
            "Point directories made": f"{len(restored_paths):,}",
            "Could not be made": f"{len(not_in_trajectory):,}",
        },
        notes,
    )

    return [PointDirectory(path) for path in restored_paths]


def offer_report(check: PointsDirectoryCheck):
    """Asks whether a report of every point which was checked should be saved, and
    writes it into the directory which was checked if so.

    The screen only shows the points which need looking at (and only the first few of
    those in full), so the report is what to keep when a set is too big to read off the
    screen or when the outcome is to be looked at later.
    """

    if not user_input_bool("Save a report of every point to file (yes/no): ", False):
        return

    report_path = check.write_report(
        Path(check.path) / REPORT_NAME.format(check.calculation_name)
    )
    print(f"\nReport written to {report_path}")
    # the menu clears the screen when it is drawn again, so wait for the path to be read
    user_input_free_flow("\nPress enter to continue: ")


def run_check(
    check_class: Type[PointsDirectoryCheck],
    notes: List[str],
    check_sequence: bool = False,
):
    """Checks the selected PointsDirectory, prints the points which are not finished and
    offers to save a report of every point.

    :param check_class: The check to run, e.g. ``GaussianCheck`` or ``AimallCheck``.
    :param notes: Sentences printed underneath the summary, explaining what the outcome
        of this particular check means and what to do about it.
    :param check_sequence: Whether to also look for points which are missing from the
        sequence of the set, i.e. which are not there to be checked at all, defaults to
        False.
    """

    check = make_check(check_class)
    if check is None:
        return

    print_problem_points(check)

    missing_points_check = find_missing_points(check.path) if check_sequence else None
    if missing_points_check is not None:
        print_missing_points(missing_points_check)

    counts = check.counts
    ichor.hpc.global_variables.LOGGER.info(
        f"{check_class.calculation_name} check of {check.path}: "
        f"{counts['OK']}/{check.npoints} points finished."
    )

    summary = {
        "PointsDirectory": check.path,
        "Points checked": f"{check.npoints:,}",
        "Finished": f"{counts['OK']:,}",
        "Missing output": f"{counts['MISSING']:,}",
        "Incomplete output": f"{counts['INCOMPLETE']:,}",
    }

    if missing_points_check is not None:
        summary["Missing from the set"] = f"{missing_points_check.nmissing:,}"
        notes = notes + [
            "A point which is missing from the set is one whose point directory is not "
            "there at all, which shows up as a hole in the sequence the points are "
            "numbered in. Use the resubmit option of this menu to write those points "
            "again out of the trajectory the set was made from and calculate them.",
            "Only the holes between the points which are there can be found here. "
            "Points which were deleted from the end of a set are found as well once the "
            "trajectory is given, which the resubmit option asks for.",
        ]

    print_summary(
        f"{check_class.calculation_name} CHECK FINISHED",
        summary,
        notes,
    )

    offer_report(check)


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

    for result in tqdm(
        check.problem_points, desc="Collecting points to resubmit", unit="point"
    ):
        point = PointDirectory(result.path)
        if not can_be_resubmitted(point):
            skipped_points.append(check.display_name(result))
            continue
        # a point directory is inside the PointsDirectory which holds it
        points_by_points_directory.setdefault(result.path.parent, []).append(point)

    return points_by_points_directory, skipped_points


def nothing_to_resubmit(
    check: PointsDirectoryCheck,
    skipped_points: List[str],
    skipped_reason: str,
):
    """Tells the user why there is nothing to submit again, which is either that every
    point is finished or that the unfinished ones cannot be calculated as they are."""

    if skipped_points:
        notes = [
            f"None of the {len(skipped_points)} unfinished points can be resubmitted, "
            f"as {skipped_reason}.",
            f"The points in question are: {shorten_names(skipped_points)}.",
        ]
    else:
        notes = [
            "Every point has the output of this calculation, so there is nothing to "
            "submit again."
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


def confirm_resubmission(
    check: PointsDirectoryCheck,
    points_by_points_directory: Dict[Path, List[PointDirectory]],
    skipped_points: List[str],
    skipped_reason: str,
    settings: dict,
    settings_menu: str,
    settings_changed: bool = False,
    nrestored: int = 0,
) -> str:
    """Shows which points would be calculated again, and with which settings, and asks
    whether to go ahead with submitting them.

    :param check: The finished check whose problem points are to be resubmitted.
    :param points_by_points_directory: The points to resubmit, as collected by
        :func:`problem_points_by_points_directory`.
    :param skipped_points: The names of the points which cannot be resubmitted.
    :param skipped_reason: Why those points cannot be resubmitted.
    :param settings: The settings the calculation would be submitted with.
    :param settings_menu: The name of the menu those settings come from.
    :param settings_changed: Whether the settings have been changed for this
        resubmission, i.e. are no longer the ones of that menu, defaults to False.
    :param nrestored: How many of the points to submit are points which were missing from
        the set and have just been written again, defaults to 0.
    :return: ``"yes"`` to submit, ``"change"`` to change the settings first, or ``"no"``
        to submit nothing.
    """

    npoints = sum(len(points) for points in points_by_points_directory.values())

    if settings_changed:
        settings_note = (
            "The settings above are the ones which have just been entered. They are "
            f"used for this resubmission only, i.e. the {settings_menu} keeps its own."
        )
    else:
        settings_note = (
            f"The settings above are the ones of the {settings_menu}. Choose 'change' "
            "to use different ones for this resubmission."
        )

    notes = [
        settings_note + " Points which are calculated again should be calculated the "
        "same way as the rest of the set, so make sure these are the settings this set "
        "was made with.",
        "The points are submitted as a job array, one job array per PointsDirectory, "
        "and the output of the unfinished points is overwritten as they are calculated "
        "again.",
    ]

    if skipped_points:
        notes.append(
            f"{len(skipped_points)} of the unfinished points are left out, as "
            f"{skipped_reason}: {shorten_names(skipped_points)}."
        )

    summary = {
        "PointsDirectory": check.path,
        "Points checked": f"{check.npoints:,}",
        "To resubmit": f"{npoints:,}",
        "Left out": f"{len(skipped_points):,}",
        "Job arrays": f"{len(points_by_points_directory)}",
    }

    if nrestored:
        summary["Made again from trajectory"] = f"{nrestored:,}"
        notes.append(
            f"{nrestored} of the points being submitted are points which were missing "
            "from the set and have just been written again, so they were not among the "
            "points which were checked."
        )

    print_summary(
        f"POINTS TO RESUBMIT TO {check.calculation_name}",
        {**summary, **settings},
        notes,
    )

    return user_input_restricted(
        ["yes", "no", "change"],
        f"Resubmit {npoints} point{'s' if npoints != 1 else ''} "
        "(type change to alter the calculation settings first): ",
        "no",
    )


# class with static methods for each menu item that calls a function.
class CheckCalculationsFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates the menu options."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        check_calculations_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def check_gaussian_calculations():
        """Checks that Gaussian has written a wavefunction for every point."""

        run_check(
            GaussianCheck,
            [
                "A point with missing output has no wfn file, so Gaussian either has "
                "not run on it yet or crashed before writing anything; a point with "
                "incomplete output has a wfn file which was not written to the end, "
                "which usually means the job ran out of time or was killed.",
                "Use the resubmit option of this menu to calculate the unfinished "
                "points again. Only those points are submitted, so the ones which are "
                "already done are not touched.",
            ],
            check_sequence=True,
        )

    @staticmethod
    def resubmit_gaussian_calculations():
        """Checks the selected PointsDirectory, writes the points which are missing from
        it again out of the trajectory it was made from, and submits both those and the
        points which are not finished back to Gaussian."""

        check = make_check(GaussianCheck)
        if check is None:
            return

        print_problem_points(check)

        # a gjf file is written from the geometry of the point, so a point which has
        # neither a geometry nor an input file has nothing that can be calculated
        points_by_points_directory, skipped_points = problem_points_by_points_directory(
            check, has_geometry
        )
        skipped_reason = (
            "they have no .xyz and no .gjf file, so there is no geometry to calculate"
        )

        # a point directory which was deleted is not there to be checked, so the points
        # which are missing from the sequence of the set are found (and written again)
        # separately from the ones which did not finish
        restored_points = restore_points_missing_from_sequence(check.path)
        for point in restored_points:
            # a point directory is inside the PointsDirectory which holds it
            points_by_points_directory.setdefault(point.path.parent, []).append(point)
        for points in points_by_points_directory.values():
            points.sort(key=lambda point: point.path.name)

        if not points_by_points_directory:
            nothing_to_resubmit(check, skipped_points, skipped_reason)
            return

        method, basis_set, ncores, overwrite_existing_gjfs = (
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_basis_set,
            submit_gaussian_menu_options.selected_number_of_cores,
            submit_gaussian_menu_options.selected_overwrite_existing_gjfs,
        )

        settings_changed = False

        while True:

            # add memory link0 to GJF, as the Submit Gaussian Menu does
            mem = (GaussianCommand.memory_per_core - 1) * ncores
            settings = {
                "Method": method,
                "Basis set": basis_set,
                "CPU cores per point": ncores,
                "Memory per point": f"{mem} GB",
                "Overwrite existing gjfs": overwrite_existing_gjfs,
            }

            answer = confirm_resubmission(
                check,
                points_by_points_directory,
                skipped_points,
                skipped_reason,
                settings,
                "Submit Gaussian Menu",
                settings_changed,
                nrestored=len(restored_points),
            )

            if answer != "change":
                break

            method = user_input_free_flow("Enter method: ", method)
            basis_set = user_input_free_flow("Enter basis set: ", basis_set)
            ncores = user_input_int("Enter number of cores: ", ncores, minimum=1)
            overwrite_existing_gjfs = user_input_bool(
                "Overwrite existing gjfs (yes/no): ", overwrite_existing_gjfs
            )
            settings_changed = True

        if answer != "yes":
            return

        print("\nSTARTING GAUSSIAN JOB SUBMISSION\n")

        link0 = [f"NProcShared={ncores}", f"Mem={mem}GB"]
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
            f"Resubmitted {npoints} unfinished points of {check.path} to Gaussian "
            f"({len(restored_points)} of them written again from a trajectory)."
        )

        summary = {
            "PointsDirectory": check.path,
            "Geometries": f"{npoints:,}",
            "Job arrays": f"{len(points_by_points_directory)}",
            "Job IDs": ", ".join(
                job_id.id if job_id else "not available" for job_id in job_ids
            ),
        }

        notes = [
            "Only the points which need calculating have been submitted, so the "
            "wavefunctions which are already there are left alone. The wfn file of "
            "a point which was cut short is overwritten when its job runs.",
            "The jobs are queued, so they will not start immediately and this menu "
            "does not wait for them. Check on them with your batch system's queue "
            "command (e.g. qstat / squeue), then run the check again to see whether "
            "they finished this time.",
        ]

        if restored_points:
            summary["Made again from trajectory"] = f"{len(restored_points):,}"
            notes.append(
                f"{len(restored_points)} of the points submitted were missing from the "
                "set and have been written again out of the trajectory it was made "
                "from, so once their jobs have run the set holds a wavefunction for "
                "every geometry it should have."
            )

        print_summary_and_pause(
            "UNFINISHED GAUSSIAN POINTS RESUBMITTED",
            {**summary, **settings},
            notes,
        )

    @staticmethod
    def check_aimall_calculations():
        """Checks that AIMAll has written the atomic files for every point."""

        run_check(
            AimallCheck,
            [
                "AIMAll writes one .int file per atom into a <point>_atomicfiles "
                "directory next to the wavefunction. A point with missing output has no "
                "such directory, so AIMAll has not run on it; a point with incomplete "
                "output is missing the .int file of one or more atoms, or has files "
                "which AIMAll leaves behind when it crashes (a .sh script or "
                "intermediate .mog files).",
                "Points without a wavefunction cannot be run through AIMAll at all, so "
                "check Gaussian first if many points are missing their atomic files. "
                "Otherwise, use the resubmit option of this menu to calculate the "
                "unfinished points again.",
            ],
        )

    @staticmethod
    def resubmit_aimall_calculations():
        """Checks the selected PointsDirectory and submits the points which are not
        finished back to AIMAll."""

        check = make_check(AimallCheck)
        if check is None:
            return

        print_problem_points(check)

        # AIMAll partitions a wavefunction, so a point without a usable one has nothing
        # to run on
        points_by_points_directory, skipped_points = problem_points_by_points_directory(
            check, has_usable_wfn
        )
        skipped_reason = (
            "Gaussian has not finished writing their wavefunction, so calculate them "
            "with the Gaussian check of this menu first"
        )

        if not points_by_points_directory:
            nothing_to_resubmit(check, skipped_points, skipped_reason)
            return

        method, ncores, naat, encomp = (
            submit_aimall_menu_options.selected_method,
            submit_aimall_menu_options.selected_number_of_cores,
            submit_aimall_menu_options.selected_naat,
            submit_aimall_menu_options.selected_encomp,
        )

        settings_changed = False

        while True:

            settings = {
                "Method": method,
                "naat setting": naat,
                "encomp setting": encomp,
                "CPU cores per point": ncores,
            }

            answer = confirm_resubmission(
                check,
                points_by_points_directory,
                skipped_points,
                skipped_reason,
                settings,
                "Submit AIMAll Menu",
                settings_changed,
            )

            if answer != "change":
                break

            method = user_input_free_flow("Enter method: ", method)
            ncores = user_input_int("Enter number of cores: ", ncores, minimum=1)
            naat = user_input_int("Select 'naat' setting: ", naat, minimum=1)
            encomp = user_input_int("Select 'encomp' setting: ", encomp)
            settings_changed = True

        if answer != "yes":
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
check_calculations_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        CheckCalculationsFunctions.select_points_directory,
    ),
    FunctionItem(
        "Check Gaussian calculations",
        CheckCalculationsFunctions.check_gaussian_calculations,
    ),
    FunctionItem(
        "Resubmit failed and missing Gaussian calculations",
        CheckCalculationsFunctions.resubmit_gaussian_calculations,
    ),
    FunctionItem(
        "Check AIMAll calculations",
        CheckCalculationsFunctions.check_aimall_calculations,
    ),
    FunctionItem(
        "Resubmit failed AIMAll calculations",
        CheckCalculationsFunctions.resubmit_aimall_calculations,
    ),
]

# initialize menu
check_calculations_menu = ConsoleMenu(
    this_menu_options=check_calculations_menu_options,
    title=CHECK_CALCULATIONS_MENU_DESCRIPTION.title,
    subtitle=CHECK_CALCULATIONS_MENU_DESCRIPTION.subtitle,
    prologue_text=CHECK_CALCULATIONS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=CHECK_CALCULATIONS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=CHECK_CALCULATIONS_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(check_calculations_menu, check_calculations_menu_items)
