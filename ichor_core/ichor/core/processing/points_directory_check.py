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
stays cheap. What a check spends its time on is the filesystem rather than the CPU, so
each point directory is listed once with :func:`os.scandir` (see :class:`DirectoryScan`)
and several points are looked at at a time (see ``nthreads``), which is what makes
checking a large set on the shared filesystem of a cluster take seconds rather than
minutes.
"""

import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Sequence, Tuple, Type, Union

from ichor.core.files import (
    GaussianOutput,
    GJF,
    Int,
    IntDirectory,
    PointDirectory,
    PointsDirectory,
    WFN,
    XTB,
    XYZ,
)
from ichor.core.files.file import File
from ichor.core.files.path_object import PathObject
from ichor.core.useful_functions import single_or_many_points_directories
from tqdm import tqdm

__all__ = [
    "PointCheckResult",
    "DirectoryScan",
    "PointsDirectoryCheck",
    "GaussianCheck",
    "AimallCheck",
    "point_directory_paths_in",
    "points_directory_paths_in",
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

# how many points are looked at at the same time. Checking a point is waiting on the
# filesystem rather than on the CPU (one listing of the point directory, and the last
# line of each of the files which were found in it), and on the shared filesystem of a
# cluster every one of those waits is a round trip over the network, so a check gets
# through the points many times quicker when it has more than one of them outstanding at
# a time. Threads are what this wants rather than processes, as a thread waiting on a
# read is not holding the GIL and there is nothing to send back and forth.
DEFAULT_NTHREADS = 16

# the geometry files which reading a PointsDirectory turns into point directories
GEOMETRY_FILETYPES = {XYZ.get_filetype(), GJF.get_filetype(), XTB.get_filetype()}

# how many points of a PointsDirectory are looked in for the atoms of the system before
# giving up on finding them. The atoms are read from the first point which has a geometry
# file that can be read, which is the first point of the set unless something is wrong
MAX_POINTS_READ_FOR_ATOM_NAMES = 20


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


def _scandir(path: Path) -> List[os.DirEntry]:
    """Lists a directory, returning the entries of one :func:`os.scandir` of it.

    Unlike ``Path.iterdir``, the entries carry what the operating system returned with
    the listing itself, so asking whether an entry is a directory does not cost another
    trip to the filesystem.

    :param path: Path of the directory to list.
    :return: The entries in it, or an empty list if it cannot be listed, i.e. it is not
        there or it cannot be read.
    """

    try:
        with os.scandir(path) as entries:
            return list(entries)
    except OSError:
        return []


class DirectoryScan:
    """The contents of one directory, from a single listing of it.

    A check needs to know which files a point directory holds and, for some of them, how
    they end. Reading it as a :class:`PointDirectory` instead builds a file object for
    every file in it (and, for the atomic files, an ``IntDirectory`` holding an ``Int``
    per atom on top of that), which a check has no use for. For a set of many thousands
    of points, doing without that is most of the time a check used to take.

    Which files are of which kind is still decided by the ``check_path`` of the classes
    which wrap them, so a check finds the same files in a directory as the rest of ichor
    would.

    :param path: Path of the directory to scan.
    """

    def __init__(self, path: Union[str, Path]):

        self.path = Path(path)
        self.name = self.path.name
        self.file_paths: List[Path] = []
        self.directory_paths: List[Path] = []

        for entry in _scandir(self.path):
            if entry.is_dir():
                self.directory_paths.append(Path(entry.path))
            else:
                self.file_paths.append(Path(entry.path))

    def files(self, file_class: Type[File]) -> List[Path]:
        """The paths of the files which are of a kind, e.g. the .wfn files.

        :param file_class: The class which wraps that kind of file, e.g. ``WFN``.
        """
        return [path for path in self.file_paths if file_class.check_path(path)]

    def directories(self, directory_class: Type[PathObject]) -> List[Path]:
        """The paths of the sub-directories which are of a kind, e.g. the directories of
        atomic files.

        :param directory_class: The class which wraps that kind of directory, e.g.
            ``IntDirectory``.
        """
        return [
            path for path in self.directory_paths if directory_class.check_path(path)
        ]

    def files_with_suffix(self, *suffixes: str) -> List[Path]:
        """The paths of the files whose suffix is one of the given ones, for the files
        which no class of ichor wraps (the .sh and .mog files AIMAll leaves behind)."""
        return [path for path in self.file_paths if path.suffix in suffixes]


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


def _is_empty(path: Path) -> bool:
    """Whether a file which is on disk has nothing in it."""

    try:
        return path.stat().st_size == 0
    except OSError:
        return False


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


def points_directory_paths_in(path: Union[str, Path]) -> List[Path]:
    """Returns the paths of the PointsDirectory-ies at a path, which can either be one
    PointsDirectory or a parent directory containing many of them.

    :param path: Path to a PointsDirectory or PointsDirectoryParent-like directory.
    :raises FileNotFoundError: If the path is not a directory on disk.
    """

    path = Path(path)

    if not path.is_dir():
        raise FileNotFoundError(
            f"{path} is not a directory, so there are no points in it to check."
        )

    if single_or_many_points_directories(path):
        return sorted(
            (p for p in path.iterdir() if PointsDirectory.check_path(p)),
            key=lambda p: p.name,
        )

    return [path]


def point_directory_paths_in(points_directory_path: Union[str, Path]) -> List[Path]:
    """Returns the paths of the point directories of one PointsDirectory, in the order
    the points are named in.

    :param points_directory_path: Path of the PointsDirectory.
    """

    points_directory_path = Path(points_directory_path)

    def point_paths(entries: List[os.DirEntry]) -> List[Path]:
        return [
            Path(entry.path)
            for entry in entries
            if entry.name.endswith(PointDirectory._suffix) and entry.is_dir()
        ]

    entries = _scandir(points_directory_path)
    paths = point_paths(entries)

    # a set which has just been written out of a trajectory holds one loose geometry file
    # per point rather than point directories, and it is reading it as a PointsDirectory
    # which makes a point directory of each of them (see PointsDirectory._parse). That is
    # the one thing which cannot be done by looking, so a set which is still in that
    # state is read in the usual way before it is checked.
    if any(
        Path(entry.name).suffix in GEOMETRY_FILETYPES and not entry.is_dir()
        for entry in entries
    ):
        PointsDirectory(points_directory_path)
        paths = point_paths(_scandir(points_directory_path))

    return sorted(paths, key=lambda p: p.name)


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
    :param nthreads: How many points to look at at the same time, defaults to
        :data:`DEFAULT_NTHREADS`. Checking a point is waiting on the filesystem, so
        having several of them outstanding at a time is what makes a check of a large set
        quick; pass 1 to check the points one after the other.
    """

    # name of the calculation being checked, used in the report
    calculation_name = "CALCULATION"

    def __init__(
        self,
        path: Union[str, Path],
        check_file_contents: bool = True,
        nthreads: int = DEFAULT_NTHREADS,
    ):

        self.path = Path(path)
        self.check_file_contents = check_file_contents
        self.nthreads = max(1, nthreads)
        self.points_directory_paths = points_directory_paths_in(self.path)
        # more than one PointsDirectory means point names can repeat, so the points are
        # reported together with the PointsDirectory they are in
        self._many_points_directories = len(self.points_directory_paths) > 1

        self.results: List[PointCheckResult] = []
        self.check()

    def check(self) -> List[PointCheckResult]:
        """Checks every point of every PointsDirectory and stores the outcome in
        ``self.results``.

        :return: The list of per-point results.
        """

        self.results = []

        # the points of every PointsDirectory being checked, gathered first so that one
        # progress bar covers the lot. This is one listing per PointsDirectory, so it is
        # quick even for a set of many thousands of points, unlike the walk over the
        # points themselves which follows it
        points = []
        for points_directory_path in self.points_directory_paths:
            point_paths = point_directory_paths_in(points_directory_path)
            self.prepare(points_directory_path, point_paths)
            points.extend(
                (points_directory_path, point_path) for point_path in point_paths
            )

        def check_one(point: Tuple[Path, Path]) -> PointCheckResult:
            points_directory_path, point_path = point
            status, problems = self.check_point(DirectoryScan(point_path))
            return PointCheckResult(
                name=point_path.name,
                path=point_path,
                points_directory=points_directory_path.name,
                status=status,
                problems=problems,
            )

        progress = tqdm(
            total=len(points),
            desc=f"Checking {self.calculation_name} output",
            unit="point",
        )

        try:
            if self.nthreads > 1 and len(points) > 1:
                with ThreadPoolExecutor(max_workers=self.nthreads) as executor:
                    # map hands back the results in the order the points were given in,
                    # so they are in the order the points are named in however the
                    # threads happened to get through them
                    for result in executor.map(check_one, points):
                        self.results.append(result)
                        progress.update()
            else:
                for point in points:
                    self.results.append(check_one(point))
                    progress.update()
        finally:
            progress.close()

        return self.results

    def prepare(self, points_directory_path: Path, point_paths: List[Path]) -> None:
        """Hook which is run once for each PointsDirectory, before any of its points are
        checked. Subclasses use it for whatever is the same for every point of a set, so
        that it is not worked out again for each of them.

        :param points_directory_path: Path of the PointsDirectory about to be checked.
        :param point_paths: The paths of its point directories.
        """

    def check_point(self, point: DirectoryScan) -> Tuple[str, List[str]]:
        """Checks a single point.

        :param point: The listed contents of the point directory to check.
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
    :param nthreads: How many points to look at at the same time.
    """

    calculation_name = "GAUSSIAN"

    def check_point(self, point: DirectoryScan) -> Tuple[str, List[str]]:
        """Checks that one point has a (finished) wavefunction file."""

        problems = []
        wfns = point.files(WFN)

        if not wfns:
            if not point.files(GJF):
                problems.append(
                    "no .wfn and no .gjf file, so the point has not been set up for Gaussian"
                )
            elif point.files(GaussianOutput):
                problems.append(
                    "no .wfn file, but a Gaussian output file is there, so look in it for errors"
                )
            else:
                problems.append("no .wfn file, so Gaussian has not run on this point")

            return MISSING, problems

        if len(wfns) > 1:
            problems.append(
                f"{len(wfns)} .wfn files found ({_shorten([w.name for w in wfns])}), "
                "only one is expected"
            )

        for wfn in wfns:
            if _is_empty(wfn):
                problems.append(f"{wfn.name} is empty")
            elif self.check_file_contents and not wfn_is_finished(wfn):
                problems.append(
                    f"{wfn.name} does not end with a total energy line, "
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
    :param nthreads: How many points to look at at the same time.
    """

    calculation_name = "AIMALL"

    def __init__(self, *args, **kwargs):

        # the atoms an .int file is expected for, by PointsDirectory. Every point of a
        # PointsDirectory is a geometry of the same system, so these are read once for
        # the whole set rather than once per point (see prepare)
        self._atom_names: Dict[Path, List[str]] = {}
        super().__init__(*args, **kwargs)

    @staticmethod
    def expected_atom_names(point_paths: Sequence[Path]) -> List[str]:
        """The names of the atoms an .int file is expected for, read from the geometry of
        the first of the given points which has one that can be read.

        Reading a geometry means parsing a file in full, which is more work than the rest
        of checking a point put together, so it is done once for the set rather than once
        for each point of it: every point of a PointsDirectory is a geometry of the same
        system, so they all have the same atoms.

        :param point_paths: The paths of the point directories of one PointsDirectory.
        :return: The names of the atoms, or an empty list if no geometry which could be
            read was found, in which case the .int files cannot be checked against the
            atoms of the system.
        """

        for point_path in point_paths[:MAX_POINTS_READ_FOR_ATOM_NAMES]:

            point = DirectoryScan(point_path)
            geometry_files = [(XYZ, path) for path in point.files(XYZ)]
            geometry_files += [(GJF, path) for path in point.files(GJF)]

            for geometry_class, geometry_path in geometry_files:
                try:
                    return [atom.name for atom in geometry_class(geometry_path).atoms]
                # a geometry file which is there but cannot be read is a problem for the
                # Gaussian side of things, here it only means trying the next one
                except Exception:
                    continue

        return []

    def prepare(self, points_directory_path: Path, point_paths: List[Path]) -> None:
        """Reads the atoms of the system which the PointsDirectory holds geometries of,
        as those are the atoms every one of its points needs an .int file for."""

        self._atom_names[points_directory_path] = self.expected_atom_names(point_paths)

    def check_point(self, point: DirectoryScan) -> Tuple[str, List[str]]:
        """Checks that one point has an atomicfiles directory holding a finished .int
        file for every atom."""

        problems = []
        int_directories = point.directories(IntDirectory)

        if not int_directories:
            if not point.files(WFN):
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
                f"({_shorten([d.name for d in int_directories])}), "
                "only one is expected"
            )

        # a point directory is inside the PointsDirectory whose atoms were read
        expected_atom_names = self._atom_names.get(point.path.parent, [])

        for int_directory_path in int_directories:

            int_directory = DirectoryScan(int_directory_path)
            # AIMAll names the .int file of an atom after the atom, e.g. o1.int for O1
            int_files_by_atom = {
                path.stem.capitalize(): path for path in int_directory.files(Int)
            }

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
            elif not int_files_by_atom:
                problems.append("the _atomicfiles directory holds no .int files")

            # AIMAll writes a .mog file while it integrates an atom and deletes it once
            # that atom is done, so one left behind means it never got there
            unfinished_atoms = sorted(
                {
                    path.stem.capitalize()
                    for path in int_directory.files_with_suffix(".mog", ".mog2")
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
                    for atom_name, int_path in int_files_by_atom.items()
                    if not _ends_with(int_path, INT_FINAL_LINE)
                )
                if truncated_atoms:
                    problems.append(
                        f"the .int file of {_shorten(truncated_atoms)} was not written "
                        "to the end, so AIMAll did not finish integrating"
                    )

        # AIMAll deletes the submission script it is given once it finishes, so one left
        # behind in the point directory means it crashed
        leftover_scripts = [path.name for path in point.files_with_suffix(".sh")]
        if leftover_scripts:
            problems.append(
                f"a .sh file is left in the point directory "
                f"({_shorten(leftover_scripts)}), so AIMAll likely crashed"
            )

        if problems:
            return INCOMPLETE, problems

        return OK, []
