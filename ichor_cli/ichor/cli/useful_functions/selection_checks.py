"""Checks that the files and directories a menu option needs have actually been selected
before the option is run.

Every selection of a menu starts out as the directory ichor is running in (see
:mod:`ichor.cli.global_menu_variables`), which is a placeholder rather than a choice, so
an option which is picked before its paths are set is handed the working directory. What
follows is rarely an error the user can make sense of: submitting a PointsDirectory which
is not one queues a job array of no tasks, splitting a trajectory which was never selected
writes out an empty PointsDirectory, and a DL_FFLUX run whose models were never selected
sets up a run directory next to whatever ichor was started in. All three look like they
worked.

The checks here are what those options run first. They only look at what is on disk, so
they cost a listing of a directory or a read of the first line of a file, and each of them
says what is wrong, which option selects the thing that is missing, and that nothing has
been done.
"""

from pathlib import Path
from typing import Any, Optional, Sequence, Union

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
    "xyz_file_selected",
    "input_file_selected",
    "directory_selected",
    "directories_selected",
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

# what to tell the user an xyz file is, when the one which is selected cannot be read
XYZ_FILE_NOTE = (
    "An xyz file gives the number of atoms on its first line, followed by a comment "
    "line and one line per atom, for each geometry in turn."
)


def _nothing_selected(path: Path) -> bool:
    """Whether a path is still the placeholder a menu starts with, i.e. nothing has been
    selected yet.

    Every selection starts out as the directory ichor is running in, which is never
    itself the file or directory being selected.
    """

    return path == Path.cwd()


def _report(
    action: str,
    what: str,
    path: Any,
    problem: str,
    notes: Sequence[str],
    select_with: Optional[str],
):
    """Tells the user that an option was not run, and what to select so that it can be.

    :param action: What the option would have done, e.g. ``"submit to Gaussian"``.
    :param what: What is missing, e.g. ``"starting geometry"``, which names the row of
        the summary the path is shown on.
    :param path: The path which was selected (or not).
    :param problem: What is wrong with it.
    :param notes: Sentences explaining what the thing which is missing is.
    :param select_with: The option which selects it, e.g. ``"Use 'Select xyz file' in
        the menu above this one."``. A general sentence is used when this is None.
    """

    if select_with is None:
        select_with = (
            f"Use the option which selects the {what} (in this menu, or in the menu "
            "above it) and try again."
        )

    print_summary_and_pause(
        f"CANNOT {action.upper()}",
        {what.capitalize(): path, "Problem": problem},
        [f"Nothing has been done, as there is no {what} to {action} with.", select_with]
        + list(notes),
    )


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
    points_directory_path: Union[str, Path],
    action: str,
    select_with: Optional[str] = None,
) -> bool:
    """Checks that the PointsDirectory an option is about to be run on is one which holds
    points, and tells the user what to select if it is not.

    :param points_directory_path: The selected PointsDirectory or parent to
        PointsDirectory-ies.
    :param action: What the option would do with it, e.g. ``"submit to Gaussian"``,
        which is used in the message so that the user is told which option was stopped.
    :param select_with: A sentence naming the option which selects it, defaults to a
        general one.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    points_directory_path = Path(points_directory_path)
    problem = _points_directory_problem(points_directory_path)

    if problem is None:
        return True

    _report(
        action,
        "PointsDirectory",
        points_directory_path,
        problem,
        [
            POINTS_DIRECTORY_NOTE,
            "If the geometries are still one trajectory file, split them into a "
            "PointsDirectory with the Split Trajectory Menu of the Property "
            "Calculation Menu first.",
        ],
        select_with,
    )

    return False


def _xyz_file_problem(xyz_path: Path, what: str) -> Optional[str]:
    """The reason the selected path cannot be read as an xyz file, or None if it can be.

    :param xyz_path: The selected .xyz file.
    :param what: What the file is to the option which needs it.
    """

    if _nothing_selected(xyz_path):
        return f"No {what} has been selected."

    if not xyz_path.exists():
        return f"{xyz_path} does not exist."

    if not xyz_path.is_file():
        return f"{xyz_path} is a directory, not a file."

    # the geometries are counted rather than read, so this is the first line of each of
    # them rather than the whole file, however long the trajectory is
    try:
        ngeometries = count_geometries_in_xyz(xyz_path)
    # a file which is not an xyz file at all does not start with a number of atoms
    except (ValueError, OSError, UnicodeDecodeError):
        return f"{xyz_path} could not be read as an xyz file."

    if not ngeometries:
        return f"{xyz_path} holds no geometries."

    return None


def xyz_file_selected(
    xyz_path: Union[str, Path],
    action: str,
    what: str = "trajectory",
    select_with: Optional[str] = None,
) -> bool:
    """Checks that the .xyz file an option is about to be run on is a file which holds
    geometries, and tells the user what to select if it is not.

    An xyz file which is not there is not an error on its own: reading one which does not
    exist gives an empty trajectory (so that geometries can be added to it and written
    out), which is what makes an option that is run before its geometries have been
    selected quietly do nothing at all.

    :param xyz_path: The selected .xyz file.
    :param action: What the option would do with it, e.g. ``"split"``, which is used in
        the message so that the user is told which option was stopped.
    :param what: What the file is to that option, e.g. ``"starting geometry"`` or
        ``"seed geometry"``, defaults to ``"trajectory"``.
    :param select_with: A sentence naming the option which selects it, defaults to a
        general one.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    xyz_path = Path(xyz_path)
    problem = _xyz_file_problem(xyz_path, what)

    if problem is None:
        return True

    _report(action, what, xyz_path, problem, [XYZ_FILE_NOTE], select_with)

    return False


def input_file_selected(
    file_path: Union[str, Path],
    action: str,
    what: str = "input file",
    select_with: Optional[str] = None,
) -> bool:
    """Checks that the file an option is about to be run on is a file which is there.

    What is in it is not looked at, which is what this is for: the file conversion menu
    reads a hundred different formats, and a Gaussian input file is whatever Gaussian
    makes of it, so there is nothing to check beyond the file itself.

    :param file_path: The selected file.
    :param action: What the option would do with it, e.g. ``"convert the file"``.
    :param what: What the file is to that option, defaults to ``"input file"``.
    :param select_with: A sentence naming the option which selects it, defaults to a
        general one.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    file_path = Path(file_path)

    if _nothing_selected(file_path):
        problem = f"No {what} has been selected."
    elif not file_path.exists():
        problem = f"{file_path} does not exist."
    elif not file_path.is_file():
        problem = f"{file_path} is a directory, not a file."
    else:
        return True

    _report(action, what, file_path, problem, [], select_with)

    return False


def directory_selected(
    directory_path: Union[str, Path],
    action: str,
    what: str,
    must_exist: bool = True,
    holds: Optional[str] = None,
    holds_description: Optional[str] = None,
    select_with: Optional[str] = None,
) -> bool:
    """Checks that the directory an option needs has been selected, and tells the user
    what to select if it has not.

    :param directory_path: The selected directory.
    :param action: What the option would do with it, e.g. ``"prepare the datasets"``.
    :param what: What the directory is to that option, e.g. ``"csv directory"`` or
        ``"model directory"``.
    :param must_exist: Whether the directory has to be there already, defaults to True.
        Pass False for a directory the option would create, where all that matters is
        that it was chosen rather than left as the working directory.
    :param holds: An optional glob which the directory has to hold something matching,
        e.g. ``"*.csv"``, so that a directory which is there but empty is caught as well.
    :param holds_description: What that glob is looking for, in words, e.g.
        ``"csv files"``, used in the message.
    :param select_with: A sentence naming the option which selects it, defaults to a
        general one.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    directory_path = Path(directory_path)

    if _nothing_selected(directory_path):
        problem = f"No {what} has been selected."
    elif not directory_path.exists():
        # a directory the option would make itself does not have to be there yet
        if not must_exist:
            return True
        problem = f"{directory_path} does not exist."
    elif not directory_path.is_dir():
        problem = f"{directory_path} is a file, not a directory."
    elif holds and not any(directory_path.glob(holds)):
        problem = (
            f"{directory_path} holds no {holds_description or holds}, so there is "
            "nothing in it to use."
        )
    else:
        return True

    _report(action, what, directory_path, problem, [], select_with)

    return False


def directories_selected(
    directory_paths: Sequence[Union[str, Path]],
    action: str,
    what: str,
    select_with: Optional[str] = None,
) -> bool:
    """Checks that at least one directory has been added to a list of them, and that each
    of the ones which were added is there.

    This is for the options which are given several directories one at a time (the models
    of each kind of molecule in a condensed phase box, for instance) rather than one
    selection which replaces the last.

    :param directory_paths: The directories which have been added.
    :param action: What the option would do with them.
    :param what: What one of them is to that option, e.g. ``"model directory"``.
    :param select_with: A sentence naming the option which adds one, defaults to a
        general one.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    directory_paths = [Path(path) for path in directory_paths]

    if not directory_paths:
        _report(
            action, what, "none added", f"No {what} has been added.", [], select_with
        )
        return False

    for directory_path in directory_paths:
        if not directory_path.is_dir():
            _report(
                action,
                what,
                directory_path,
                f"{directory_path} is not a directory.",
                [
                    f"{len(directory_paths)} {what}s have been added, and this one "
                    "cannot be used. Clear them and add them again."
                ],
                select_with,
            )
            return False

    return True
