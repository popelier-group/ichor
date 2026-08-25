"""Checks that the file or directory a menu option needs has actually been selected
before the option is run.

Every selection of a menu starts out as the directory ichor is running in (see
:mod:`ichor.cli.global_menu_variables`), which is a placeholder rather than a choice, so
an option which is picked before its path is set is handed the working directory. What
follows is rarely an error the user can make sense of: submitting a PointsDirectory which
is not one queues a job array of no tasks, and splitting a trajectory which was never
selected writes out an empty PointsDirectory, both of which look like they worked.

The checks here are what those options run first. They only look at what is on disk, so
they cost a listing of a directory or a read of the first line of a file, and they say
what is wrong and what to do about it rather than only that something is.
"""

from pathlib import Path
from typing import Optional, Union

from ichor.cli.useful_functions.summary import print_summary_and_pause
from ichor.core.files import (
    count_geometries_in_xyz,
    GJF,
    PointDirectory,
    PointsDirectory,
    PointsDirectoryParent,
    XTB,
    XYZ,
)

__all__ = [
    "points_directory_selected",
    "trajectory_selected",
]

# what a PointsDirectory holds one of per point: a point directory, or (for a set which
# has just been written out of a trajectory and not yet read as a PointsDirectory) a
# loose geometry file which becomes one when it is read
GEOMETRY_FILETYPES = {XYZ.get_filetype(), GJF.get_filetype(), XTB.get_filetype()}

# what to tell the user a PointsDirectory is, when the one which is selected is not one
POINTS_DIRECTORY_NOTE = (
    "A PointsDirectory is the directory of point directories which the Split Trajectory "
    f"Menu writes (its name ends in {PointsDirectory._suffix}), or the parent directory "
    f"holding several of them (which ends in {PointsDirectoryParent._suffix})."
)


def _nothing_selected(path: Path) -> bool:
    """Whether a path is still the placeholder a menu starts with, i.e. nothing has been
    selected yet.

    Every selection starts out as the directory ichor is running in, which is never
    itself the file or directory being selected.
    """

    return path == Path.cwd()


def _npoints_in(points_directory_path: Path) -> int:
    """How many points a PointsDirectory-like directory holds, counted from one listing
    of it and without reading any of them.

    A set which has just been written out of a trajectory holds one loose geometry file
    per point rather than point directories (reading it as a ``PointsDirectory`` is what
    turns those into point directories), so both are counted.

    :param points_directory_path: Path of the directory to count the points of.
    """

    npoints = 0

    for path in points_directory_path.iterdir():
        if path.name.endswith(PointDirectory._suffix) and path.is_dir():
            npoints += 1
        elif path.suffix in GEOMETRY_FILETYPES and path.is_file():
            npoints += 1

    return npoints


def _points_directory_problem(points_directory_path: Path) -> Optional[str]:
    """The reason the selected path cannot be calculated, or None if it can be.

    :param points_directory_path: The selected PointsDirectory or parent to
        PointsDirectory-ies.
    """

    if _nothing_selected(points_directory_path):
        return "No PointsDirectory has been selected."

    if not points_directory_path.exists():
        return f"{points_directory_path} does not exist."

    if not points_directory_path.is_dir():
        return f"{points_directory_path} is a file, not a directory."

    # a parent holds PointsDirectory-ies, which hold the points themselves
    if points_directory_path.suffix == PointsDirectoryParent._suffix:

        points_directories = [
            path
            for path in points_directory_path.iterdir()
            if PointsDirectory.check_path(path)
        ]
        if not points_directories:
            return (
                f"{points_directory_path} holds no PointsDirectory-ies, so there are no "
                "points in it."
            )
        if not any(_npoints_in(path) for path in points_directories):
            return (
                f"None of the {len(points_directories)} PointsDirectory-ies in "
                f"{points_directory_path} hold any points."
            )

        return None

    if not _npoints_in(points_directory_path):
        return f"{points_directory_path} holds no points."

    return None


def points_directory_selected(
    points_directory_path: Union[str, Path], action: str
) -> bool:
    """Checks that the PointsDirectory an option is about to be run on is one which holds
    points, and tells the user what to select if it is not.

    :param points_directory_path: The selected PointsDirectory or parent to
        PointsDirectory-ies.
    :param action: What the option would do with it, e.g. ``"submit to Gaussian"``,
        which is used in the message so that the user is told which option was stopped.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    points_directory_path = Path(points_directory_path)
    problem = _points_directory_problem(points_directory_path)

    if problem is None:
        return True

    print_summary_and_pause(
        "NOTHING TO CALCULATE",
        {
            "PointsDirectory": points_directory_path,
            "Problem": problem,
        },
        [
            f"There are no points to {action}, so nothing has been done.",
            "Use the option at the top of this menu to select the PointsDirectory "
            f"first. {POINTS_DIRECTORY_NOTE}",
            "If the geometries are still one trajectory file, split them into a "
            "PointsDirectory with the Split Trajectory Menu of the Property Calculation "
            "Menu first.",
        ],
    )

    return False


def _trajectory_problem(trajectory_path: Path) -> Optional[str]:
    """The reason the selected path cannot be read as a trajectory, or None if it can be.

    :param trajectory_path: The selected trajectory (.xyz) file.
    """

    if _nothing_selected(trajectory_path):
        return "No trajectory file has been selected."

    if not trajectory_path.exists():
        return f"{trajectory_path} does not exist."

    if not trajectory_path.is_file():
        return f"{trajectory_path} is a directory, not a file."

    # the geometries are counted rather than read, so this is the first line of each of
    # them rather than the whole file, however long the trajectory is
    try:
        ngeometries = count_geometries_in_xyz(trajectory_path)
    # a file which is not an xyz file at all does not start with a number of atoms
    except (ValueError, OSError, UnicodeDecodeError):
        return (
            f"{trajectory_path} could not be read as an xyz file. An xyz file gives the "
            "number of atoms on its first line, followed by a comment line and one line "
            "per atom, for each geometry in turn."
        )

    if not ngeometries:
        return f"{trajectory_path} holds no geometries."

    return None


def trajectory_selected(trajectory_path: Union[str, Path], action: str) -> bool:
    """Checks that the trajectory an option is about to be run on is a file which holds
    geometries, and tells the user what to select if it is not.

    A trajectory which is not there is not an error on its own: reading one which does
    not exist gives an empty trajectory (so that geometries can be added to it and
    written out), which is what makes an option that is run before a trajectory has been
    selected quietly do nothing at all.

    :param trajectory_path: The selected trajectory (.xyz) file.
    :param action: What the option would do with it, e.g. ``"split"``, which is used in
        the message so that the user is told which option was stopped.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    trajectory_path = Path(trajectory_path)
    problem = _trajectory_problem(trajectory_path)

    if problem is None:
        return True

    print_summary_and_pause(
        "NO GEOMETRIES TO USE",
        {
            "Trajectory": trajectory_path,
            "Problem": problem,
        },
        [
            f"There are no geometries to {action}, so nothing has been done.",
            "Use the option at the top of this menu to select the trajectory file "
            "first. A trajectory is an .xyz file holding one or more geometries, such "
            "as the output of a molecular dynamics run or of the sampling menu.",
        ],
    )

    return False
