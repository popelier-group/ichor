"""Checks that the Gaussian and AIMAll calculations of a PointsDirectory have finished.

A property calculation is done in two steps: Gaussian writes a wavefunction (.wfn) file
for every geometry, and AIMAll then partitions each of those wavefunctions into atomic
basins, writing one .int file per atom into a ``<point>_atomicfiles`` directory next to
the wavefunction. Both steps are submitted as job arrays of many independent tasks, of
which a few tend to fail or to be killed by the queue, so before the results are
collected into a database it is worth knowing which points, if any, are missing or
incomplete.

The checks only look at the files themselves, i.e. no wavefunction or .int file is fully
parsed (only the last line of a file is read, to see whether the program that wrote it
got to the end), so that checking a PointsDirectory containing many thousands of points
stays cheap.
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Union

from ichor.core.files import PointDirectory, PointsDirectory, PointsDirectoryParent
from ichor.core.useful_functions import single_or_many_points_directories

__all__ = [
    "PointCheckResult",
    "PointsDirectoryCheck",
    "GaussianCheck",
    "AimallCheck",
    "points_directories_in",
    "wfn_is_finished",
    "OK",
    "MISSING",
    "INCOMPLETE",
]

# the point has everything the checked calculation should have written
OK = "OK"
# the calculation has not written its main output at all (no .wfn / no _atomicfiles)
MISSING = "MISSING"
# the output is there, but it is incomplete or the program that wrote it crashed
INCOMPLETE = "INCOMPLETE"

# the last line Gaussian writes into a .wfn file, and the last line AIMAll writes into an
# .int file. A file which does not end with these was cut short.
WFN_FINAL_LINE = "TOTAL ENERGY ="
INT_FINAL_LINE = "AIMInt is Done."

# how many names of atoms/files are named in a problem before it is cut short, so that
# the report of a system with many atoms stays readable
MAX_NAMES_IN_PROBLEM = 6


@dataclass
class PointCheckResult:
    """The outcome of checking one point (one PointDirectory).

    :param name: The name of the point directory.
    :param path: The path of the point directory.
    :param points_directory: The name of the PointsDirectory the point is in, which
        matters when many PointsDirectory-ies are checked at once.
    :param status: One of ``"OK"``, ``"MISSING"`` or ``"INCOMPLETE"``.
    :param problems: The problems found with this point, empty if it is fine.
    """

    name: str
    path: Path
    points_directory: str = ""
    status: str = OK
    problems: List[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """Whether the point has everything the checked calculation should have written."""
        return self.status == OK


def _as_list(attribute) -> list:
    """Returns the contents of an AnnotatedDirectory attribute as a list.

    Contents of an ``AnnotatedDirectory`` (such as a PointDirectory) are
    ``OptionalContent`` when they are not on disk, a single instance when one file
    matches and a list of instances when several do, so this flattens all three cases
    into a list.
    """

    if not attribute:
        return []
    if isinstance(attribute, list):
        return attribute

    return [attribute]


def _last_line(path: Path, nbytes: int = 1024) -> str:
    """Returns the last non-empty line of a file, without reading the whole file.

    :param path: Path to the file.
    :param nbytes: How many bytes at the end of the file to look in, defaults to 1024.
        A file shorter than this is read in full.
    :return: The last non-empty line, or an empty string if the file is empty or cannot
        be read.
    """

    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            file_size = f.tell()
            f.seek(max(file_size - nbytes, 0))
            chunk = f.read()
    except OSError:
        return ""

    lines = [
        line for line in chunk.decode(errors="ignore").splitlines() if line.strip()
    ]

    return lines[-1] if lines else ""


def _ends_with(path: Path, final_line: str) -> bool:
    """Whether the last line of a file contains the line which the program that wrote
    the file ends with, i.e. whether the file was written all the way to the end."""
    return final_line in _last_line(path)


def wfn_is_finished(path: Union[str, Path]) -> bool:
    """Whether a .wfn file was written all the way to the end by Gaussian, i.e. whether
    it ends with the total energy line.

    A wavefunction which was cut short (or which is not there at all) cannot be used, so
    this is what decides whether a point is finished as far as Gaussian is concerned, and
    whether it can be handed to AIMAll.

    :param path: Path to the .wfn file.
    """

    return _ends_with(Path(path), WFN_FINAL_LINE)


def _shorten(names: Sequence[str]) -> str:
    """Formats a list of names for a problem, cutting it short if it is a long one."""

    names = list(names)
    if len(names) > MAX_NAMES_IN_PROBLEM:
        return (
            ", ".join(names[:MAX_NAMES_IN_PROBLEM])
            + f" (and {len(names) - MAX_NAMES_IN_PROBLEM} more)"
        )

    return ", ".join(names)


def points_directories_in(path: Union[str, Path]) -> List[PointsDirectory]:
    """Returns the PointsDirectory-ies at a path, which can either be one
    PointsDirectory or a parent directory containing many of them.

    :param path: Path to a PointsDirectory or PointsDirectoryParent-like directory.
    """

    path = Path(path)

    if single_or_many_points_directories(path):
        return list(PointsDirectoryParent(path))

    return [PointsDirectory(path)]


class PointsDirectoryCheck:
    """Base class for checking every point of one or many PointsDirectory-ies for the
    output of a calculation. Subclasses implement :meth:`check_point`, which decides
    what, if anything, is missing from a single point.

    :param path: Path to a PointsDirectory, or to a parent directory containing many
        PointsDirectory-ies, whose points are to be checked.
    :param check_file_contents: Whether to also check that the files which are there were
        written to the end (i.e. that the program which wrote them was not cut short),
        defaults to True. This reads the last line of every file, so it is slower than
        only checking that the files exist.
    """

    # name of the calculation being checked, used in the report
    calculation_name = "CALCULATION"

    def __init__(
        self,
        path: Union[str, Path],
        check_file_contents: bool = True,
    ):

        self.path = Path(path)
        self.check_file_contents = check_file_contents
        self.points_directories = points_directories_in(self.path)
        # more than one PointsDirectory means point names can repeat, so the points are
        # reported together with the PointsDirectory they are in
        self._many_points_directories = len(self.points_directories) > 1

        self.results: List[PointCheckResult] = []
        self.check()

    def check(self) -> List[PointCheckResult]:
        """Checks every point of every PointsDirectory and stores the outcome in
        ``self.results``.

        :return: The list of per-point results.
        """

        self.results = []

        for points_directory in self.points_directories:
            for point in points_directory:
                status, problems = self.check_point(point)
                self.results.append(
                    PointCheckResult(
                        name=point.path.name,
                        path=point.path,
                        points_directory=points_directory.path.name,
                        status=status,
                        problems=problems,
                    )
                )

        return self.results

    def check_point(self, point: PointDirectory) -> Tuple[str, List[str]]:
        """Checks a single point.

        :param point: The PointDirectory to check.
        :return: The status of the point and the list of problems found with it.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement check_point."
        )

    @property
    def npoints(self) -> int:
        """The number of points which were checked."""
        return len(self.results)

    @property
    def counts(self) -> Dict[str, int]:
        """The number of points with each status."""

        counts = {OK: 0, MISSING: 0, INCOMPLETE: 0}
        for result in self.results:
            counts[result.status] = counts.get(result.status, 0) + 1

        return counts

    @property
    def problem_points(self) -> List[PointCheckResult]:
        """The results of the points which are missing something."""
        return [result for result in self.results if not result.ok]

    def display_name(self, result: PointCheckResult) -> str:
        """The name a point is reported under, which includes the PointsDirectory it is
        in when many PointsDirectory-ies were checked at once."""

        if self._many_points_directories:
            return f"{result.points_directory}/{result.name}"

        return result.name

    def report(self, include_ok: bool = True) -> str:
        """Builds a human readable report of the check.

        The report contains one line per point, giving what is missing from it (if
        anything), followed by how many points were finished, how many are missing the
        output entirely and how many have incomplete output.

        :param include_ok: Whether to include the points which are fine, defaults to
            True. Setting this to False gives a report of only the points which need
            looking at, which is what is worth printing for a large PointsDirectory.
        :return: The report as a string.
        """

        results = self.results if include_ok else self.problem_points

        # point names are the system name plus an index, so the column is sized to the
        # points actually being reported rather than to a fixed width
        name_width = max(
            [len(self.display_name(result)) for result in results] + [len("POINT")]
        )

        lines = [f"{self.calculation_name} CHECK: {self.path.absolute()}", ""]
        lines.append(f"{'POINT':<{name_width}}  {'STATUS':<10}  PROBLEMS")

        for result in results:
            problems = "; ".join(result.problems) if result.problems else "-"
            lines.append(
                f"{self.display_name(result):<{name_width}}  "
                f"{result.status:<10}  {problems}"
            )

        if not results:
            lines.append("(no points to report)")

        counts = self.counts
        lines.append("")
        lines.append(f"{'Points checked':<20} {self.npoints:>10}")
        lines.append(f"{'Finished':<20} {counts[OK]:>10}")
        lines.append(f"{'Missing output':<20} {counts[MISSING]:>10}")
        lines.append(f"{'Incomplete output':<20} {counts[INCOMPLETE]:>10}")

        return "\n".join(lines) + "\n"

    def write_report(self, path: Union[str, Path]) -> Path:
        """Writes the report of :meth:`report` (including the points which are fine) to
        a file.

        :param path: Path of the report file.
        :return: The path the report was written to.
        """

        path = Path(path)

        with open(path, "w") as f:
            f.write(self.report())

        return path


class GaussianCheck(PointsDirectoryCheck):
    """Checks that Gaussian has written a wavefunction for every point of a
    PointsDirectory (or of many PointsDirectory-ies).

    A point is ``MISSING`` when it has no .wfn file at all, i.e. Gaussian has not run on
    it (or crashed before writing anything), and ``INCOMPLETE`` when the .wfn file is
    there but was not written to the end, which happens when a job runs out of time or is
    killed. Both need the point to be submitted to Gaussian again; an incomplete point
    needs the recalculate option as well, as the file which is there is unusable but
    would otherwise be taken for a finished wavefunction.

    Example usage:

    .. code-block:: python

        check = GaussianCheck("TRAINING_SET.pointsdir")
        print(check.report())

    :param path: Path to a PointsDirectory, or to a parent directory containing many
        PointsDirectory-ies.
    :param check_file_contents: Whether to also check that each .wfn file ends with the
        total energy line Gaussian finishes it with, defaults to True.
    """

    calculation_name = "GAUSSIAN"

    def check_point(self, point: PointDirectory) -> Tuple[str, List[str]]:
        """Checks that one point has a (finished) wavefunction file."""

        problems = []
        wfns = _as_list(point.wfn)

        if not wfns:
            if not _as_list(point.gjf):
                problems.append(
                    "no .wfn and no .gjf file, so the point has not been set up for Gaussian"
                )
            elif _as_list(point.gaussian_output):
                problems.append(
                    "no .wfn file, but a Gaussian output file is there, so look in it for errors"
                )
            else:
                problems.append("no .wfn file, so Gaussian has not run on this point")

            return MISSING, problems

        if len(wfns) > 1:
            problems.append(
                f"{len(wfns)} .wfn files found ({_shorten([w.path.name for w in wfns])}), "
                "only one is expected"
            )

        for wfn in wfns:
            if wfn.path.stat().st_size == 0:
                problems.append(f"{wfn.path.name} is empty")
            elif self.check_file_contents and not wfn_is_finished(wfn.path):
                problems.append(
                    f"{wfn.path.name} does not end with a total energy line, "
                    "so Gaussian did not finish writing it"
                )

        if problems:
            return INCOMPLETE, problems

        return OK, []


class AimallCheck(PointsDirectoryCheck):
    """Checks that AIMAll has written the atomic files for every point of a
    PointsDirectory (or of many PointsDirectory-ies).

    A point is ``MISSING`` when it has no ``<point>_atomicfiles`` directory, i.e. AIMAll
    has not run on it, and ``INCOMPLETE`` when that directory is there but does not hold
    a finished .int file for every atom of the system. AIMAll also leaves traces of a
    crash behind, which are looked for here as well: the .sh file it deletes when it
    finishes, and the intermediate .mog files it writes while integrating an atom.

    Example usage:

    .. code-block:: python

        check = AimallCheck("TRAINING_SET.pointsdir")
        print(check.report(include_ok=False))

    :param path: Path to a PointsDirectory, or to a parent directory containing many
        PointsDirectory-ies.
    :param check_file_contents: Whether to also check that each .int file ends with the
        line AIMAll finishes it with, defaults to True.
    """

    calculation_name = "AIMALL"

    @staticmethod
    def expected_atom_names(point: PointDirectory) -> List[str]:
        """The names of the atoms an .int file is expected for, read from the geometry of
        the point. Returns an empty list if the point has no geometry file which can be
        read, in which case the .int files cannot be checked against the atoms."""

        for geometry_file in _as_list(point.xyz) + _as_list(point.gjf):
            try:
                return [atom.name for atom in geometry_file.atoms]
            # a geometry file which is there but cannot be read is a problem for the
            # Gaussian side of things, here it only means the atoms are unknown
            except Exception:
                continue

        return []

    def check_point(self, point: PointDirectory) -> Tuple[str, List[str]]:
        """Checks that one point has an atomicfiles directory holding a finished .int
        file for every atom."""

        problems = []
        int_directories = _as_list(point.ints)

        if not int_directories:
            if not _as_list(point.wfn):
                problems.append(
                    "no _atomicfiles directory and no .wfn file, so AIMAll had nothing to run on"
                )
            else:
                problems.append(
                    "no _atomicfiles directory, so AIMAll has not run on this point"
                )

            return MISSING, problems

        if len(int_directories) > 1:
            problems.append(
                f"{len(int_directories)} _atomicfiles directories found "
                f"({_shorten([d.path.name for d in int_directories])}), "
                "only one is expected"
            )

        expected_atom_names = self.expected_atom_names(point)

        for int_directory in int_directories:

            int_files = _as_list(int_directory.ints)
            # AIMAll names the .int file of an atom after the atom, e.g. o1.int for O1
            int_files_by_atom = {f.path.stem.capitalize(): f for f in int_files}

            if expected_atom_names:
                missing_atoms = [
                    atom_name
                    for atom_name in expected_atom_names
                    if atom_name not in int_files_by_atom
                ]
                if missing_atoms:
                    problems.append(
                        f"no .int file for {len(missing_atoms)} of "
                        f"{len(expected_atom_names)} atoms ({_shorten(missing_atoms)})"
                    )
            elif not int_files:
                problems.append("the _atomicfiles directory holds no .int files")

            # AIMAll writes a .mog file while it integrates an atom and deletes it once
            # that atom is done, so one left behind means it never got there
            unfinished_atoms = sorted(
                {
                    f.stem.capitalize()
                    for f in int_directory.path.iterdir()
                    if f.suffix in (".mog", ".mog2")
                }
            )
            if unfinished_atoms:
                problems.append(
                    f"intermediate .mog files left for {_shorten(unfinished_atoms)}, "
                    "so AIMAll crashed or is still running"
                )

            if self.check_file_contents:
                truncated_atoms = sorted(
                    atom_name
                    for atom_name, int_file in int_files_by_atom.items()
                    if not _ends_with(int_file.path, INT_FINAL_LINE)
                )
                if truncated_atoms:
                    problems.append(
                        f"the .int file of {_shorten(truncated_atoms)} was not written "
                        "to the end, so AIMAll did not finish integrating"
                    )

        # AIMAll deletes the submission script it is given once it finishes, so one left
        # behind in the point directory means it crashed
        leftover_scripts = [f.name for f in point.path.iterdir() if f.suffix == ".sh"]
        if leftover_scripts:
            problems.append(
                f"a .sh file is left in the point directory "
                f"({_shorten(leftover_scripts)}), so AIMAll likely crashed"
            )

        if problems:
            return INCOMPLETE, problems

        return OK, []
