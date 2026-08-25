"""Finds the points which have gone missing from a PointsDirectory, and makes them again
from the trajectory the set was written out of.

The points of a set are named after the geometry they came from: the geometries of a
trajectory are written out in order as ``SYSTEM_NAME0000``, ``SYSTEM_NAME0001`` and so on
(see :meth:`ichor.core.files.Trajectory.to_dir`), so a point directory which has been
deleted leaves a hole in that sequence which can be seen without knowing anything else
about the set. That is what this finds: a set of 1000 geometries which only has 998 point
directories, or which is numbered up to 0999 but has nothing at 0143 and 0144, is missing
points, and neither the Gaussian check nor the AIMAll check can say so, as those can only
look at the point directories which are there.

The geometry of a point which has gone missing is still in the trajectory the set was
made from, so it can be put back: the hole in the sequence says which geometry of the
trajectory it was, that geometry is read out of the trajectory (see
:func:`ichor.core.files.read_geometries_from_xyz`), and the point directory is written
again exactly as it was written the first time, ready to be submitted to Gaussian.

Before any of that is done, the trajectory which is given is checked against the points
which are still there (see :func:`matching_geometries`), because writing the geometries
of some other trajectory into the holes of a set would be far worse than leaving the
holes in it.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
from ichor.core.atoms import Atoms
from ichor.core.common.io import mkdir
from ichor.core.files import PointDirectory, read_geometries_from_xyz, XYZ
from ichor.core.processing.points_directory_check import (
    DirectoryScan,
    point_directory_paths_in,
    points_directory_paths_in,
)

__all__ = [
    "point_geometry",
    "PointName",
    "parse_point_name",
    "MissingPoint",
    "PointSequence",
    "MissingPointsCheck",
    "geometries_match",
    "matching_geometries",
    "points_are_centred",
    "restore_missing_points",
]

# the name of a point is the name of the system followed by the position of its geometry
# in the trajectory the set was made from, padded with zeros to a fixed width
POINT_NAME_PATTERN = re.compile(r"^(?P<system_name>.*?)(?P<index>\d+)$")

# how far apart two geometries can be, in Angstroms, and still be taken for the same
# geometry. The coordinates of a set are written out with eight decimal places, so this
# is loose enough for a trajectory which was written out with fewer of them
GEOMETRY_TOLERANCE = 1e-4

# how many of the points which are still there are compared against the trajectory to
# decide whether it is the trajectory the set was made from
DEFAULT_NSAMPLES = 10


@dataclass
class PointName:
    """The name of a point, split into what it is made of.

    :param system_name: The name of the system, i.e. everything before the number.
    :param index: The number the name ends with, which is the position of the geometry of
        the point in the trajectory the set was made from.
    :param width: How many digits that number is written with, so that a name which is
        made again is padded the same way as the rest of the set.
    """

    system_name: str
    index: int
    width: int

    def name_of(self, index: int) -> str:
        """The name a point at a position in the sequence has, e.g. ``WATER0143``."""
        return f"{self.system_name}{index:0{self.width}d}"


def parse_point_name(name: str) -> Optional[PointName]:
    """Splits the name of a point into the name of the system and the position of its
    geometry in the trajectory the set was made from.

    :param name: The name of a point, with or without the point directory suffix,
        e.g. ``WATER0143.pointdir`` or ``WATER0143``.
    :return: The parts of the name, or None if it does not end with a number and so says
        nothing about where the point belongs in the sequence.
    """

    if name.endswith(PointDirectory._suffix):
        name = name[: -len(PointDirectory._suffix)]

    match = POINT_NAME_PATTERN.match(name)
    if not match:
        return None

    digits = match.group("index")

    return PointName(match.group("system_name"), int(digits), len(digits))


@dataclass
class MissingPoint:
    """A point which is missing from the sequence of a set.

    :param name: The name the point directory would have, e.g. ``WATER0143``.
    :param index: Its position in the sequence, which is also the position of its
        geometry in the trajectory the set was made from.
    :param points_directory: The path of the PointsDirectory it belongs in, which is the
        one holding the points on either side of the hole.
    """

    name: str
    index: int
    points_directory: Path

    @property
    def path(self) -> Path:
        """The path the point directory would be at."""
        return self.points_directory / (self.name + PointDirectory._suffix)


@dataclass
class PointSequence:
    """The points of one system, in the order they were written out of a trajectory.

    A PointsDirectory holds one of these. A parent directory of PointsDirectory-ies holds
    one per system: a trajectory which was split into chunks
    (:meth:`ichor.core.files.Trajectory.to_dirs`) numbers its points across the chunks
    rather than within them, so the chunks of one system are one sequence, while unrelated
    sets which happen to sit next to each other are not.

    :param system_name: The name of the system the points are geometries of.
    :param width: How many digits the points are numbered with.
    :param stride: The step between one point and the next, which is 1 for a set of every
        geometry of a trajectory and n for a set of every nth geometry of one.
    :param points_directory_paths: The PointsDirectory-ies the points are spread over.
    :param present_indices: The positions of the points which are there, in order.
    :param present_point_paths: The paths of the points which are there, in the same
        order, which is what a trajectory is checked against before it is used to make
        the missing ones again.
    :param missing: The points which are missing from the sequence.
    """

    system_name: str
    width: int
    stride: int
    points_directory_paths: List[Path] = field(default_factory=list)
    present_indices: List[int] = field(default_factory=list)
    present_point_paths: List[Path] = field(default_factory=list)
    missing: List[MissingPoint] = field(default_factory=list)

    @property
    def npresent(self) -> int:
        """How many points of the sequence are there."""
        return len(self.present_indices)

    @property
    def nmissing(self) -> int:
        """How many points of the sequence are missing."""
        return len(self.missing)

    @property
    def first_index(self) -> int:
        """The position of the first point of the sequence."""
        return self.present_indices[0] if self.present_indices else 0

    @property
    def last_index(self) -> int:
        """The position of the last point which is there."""
        return self.present_indices[-1] if self.present_indices else 0


def _stride(indices: Sequence[int]) -> int:
    """The step between one point of a set and the next.

    A set made of every geometry of a trajectory is numbered 0, 1, 2..., and one made of
    every nth geometry of one is numbered 0, n, 2n... (the points keep the position of
    their geometry in the trajectory, see ``Trajectory.to_dir``), so the step is the
    smallest gap between two points which are next to each other: a gap which is bigger
    than that is a point which is missing, and no two points which are both there can be
    closer together than the step the set was made with.
    """

    if len(indices) < 2:
        return 1

    return min(b - a for a, b in zip(indices, indices[1:]))


def _expected_indices(
    present_indices: Sequence[int],
    stride: int,
    ngeometries: Optional[int] = None,
    every: int = 1,
) -> range:
    """The positions the points of a sequence should be at.

    Without the trajectory, the sequence can only be expected to reach as far as the last
    point which is there, so points which were deleted from the end of a set are not
    found. Given how many geometries the trajectory has, it is known where the sequence
    should end, so those are found as well.

    :param present_indices: The positions of the points which are there, in order.
    :param stride: The step between one point and the next.
    :param ngeometries: How many geometries the trajectory the set was made from holds,
        defaults to None (i.e. it is not known).
    :param every: How many geometries of the trajectory each point of the set steps over,
        which is 1 unless the set was written out in chunks from every nth geometry of
        the trajectory, defaults to 1.
    """

    if not present_indices:
        return range(0)

    if ngeometries is None:
        end = present_indices[-1] + 1
    else:
        # a point numbered i is the geometry at i * every of the trajectory, so the
        # sequence runs out when there is no such geometry left
        end = ngeometries if every == 1 else -(-ngeometries // every)

    return range(present_indices[0], end, stride)


class MissingPointsCheck:
    """Finds the points which are missing from the sequence of one PointsDirectory (or of
    a parent directory holding many of them).

    Only the names of the point directories are looked at, so this is one listing per
    PointsDirectory however many points the set holds.

    Example usage:

    .. code-block:: python

        check = MissingPointsCheck("TRAINING_SET.pointsdir")
        print([point.name for point in check.missing])

    :param path: Path to a PointsDirectory, or to a parent directory containing many
        PointsDirectory-ies.
    :param ngeometries: How many geometries the trajectory the set was made from holds,
        defaults to None. Without it, points which were deleted from the end of a set
        cannot be told apart from a set which was made from part of a trajectory, so only
        the holes between the points which are there are found.
    :param every: How many geometries of the trajectory each point of the set steps over,
        defaults to 1. This is only ever anything else for a set which was written out in
        chunks from every nth geometry of a trajectory
        (:meth:`ichor.core.files.Trajectory.to_dirs`), whose points are numbered one
        after the other rather than by where their geometry is in the trajectory.
    """

    def __init__(
        self,
        path: Union[str, Path],
        ngeometries: Optional[int] = None,
        every: int = 1,
    ):

        self.path = Path(path)
        self.ngeometries = ngeometries
        self.every = every
        self.points_directory_paths = points_directory_paths_in(self.path)

        self.sequences: List[PointSequence] = []
        # the points whose name does not end with a number, which say nothing about
        # where they belong in a sequence
        self.unnamed_points: List[Path] = []

        self.check()

    def check(self) -> List[PointSequence]:
        """Looks at the name of every point directory and works out which points are
        missing from between them.

        :return: The sequences which were found, one per system.
        """

        self.sequences = []
        self.unnamed_points = []

        # the points of every system which was found, by the name of the system and the
        # width its points are numbered with. Two sets of the same system which are
        # numbered differently were made separately, so they are separate sequences
        points: Dict[Tuple[str, int], Dict[int, Path]] = {}

        for points_directory_path in self.points_directory_paths:
            for point_path in point_directory_paths_in(points_directory_path):

                point_name = parse_point_name(point_path.name)
                if point_name is None:
                    self.unnamed_points.append(point_path)
                    continue

                key = (point_name.system_name, point_name.width)
                points.setdefault(key, {})[point_name.index] = points_directory_path

        for (system_name, width), points_by_index in points.items():
            self.sequences.append(self._sequence(system_name, width, points_by_index))

        return self.sequences

    def _sequence(
        self, system_name: str, width: int, points_by_index: Dict[int, Path]
    ) -> PointSequence:
        """Works out the step of one sequence of points and which of them are missing."""

        present_indices = sorted(points_by_index)
        stride = _stride(present_indices)
        point_name = PointName(system_name, 0, width)

        sequence = PointSequence(
            system_name=system_name,
            width=width,
            stride=stride,
            points_directory_paths=sorted(
                set(points_by_index.values()), key=lambda p: p.name
            ),
            present_indices=present_indices,
            present_point_paths=[
                points_by_index[index]
                / (point_name.name_of(index) + PointDirectory._suffix)
                for index in present_indices
            ],
        )

        expected_indices = _expected_indices(
            present_indices, stride, self.ngeometries, self.every
        )

        # the PointsDirectory a missing point belongs in is the one which holds the point
        # before it, which is the one it would have been written into when the set was
        # made. A set which is one PointsDirectory has only the one to choose from; a set
        # which was split into chunks has the point before and the point after a hole in
        # the same chunk, unless the hole is at the boundary between two of them
        points_directory = points_by_index[present_indices[0]]

        for index in expected_indices:
            if index in points_by_index:
                points_directory = points_by_index[index]
                continue
            sequence.missing.append(
                MissingPoint(
                    name=point_name.name_of(index),
                    index=index,
                    points_directory=points_directory,
                )
            )

        return sequence

    @property
    def missing(self) -> List[MissingPoint]:
        """Every point which is missing, over all of the sequences which were found."""
        return [point for sequence in self.sequences for point in sequence.missing]

    @property
    def nmissing(self) -> int:
        """How many points are missing."""
        return len(self.missing)

    @property
    def npresent(self) -> int:
        """How many points are there."""
        return sum(sequence.npresent for sequence in self.sequences)

    @property
    def present_point_paths(self) -> List[Path]:
        """The paths of the points which are there, over all of the sequences."""
        return [
            path for sequence in self.sequences for path in sequence.present_point_paths
        ]


def point_geometry(point_path: Path) -> Optional[Atoms]:
    """Reads the geometry of a point which is on disk.

    :param point_path: The path of the point directory.
    :return: The geometry in its .xyz file, or None if it has no .xyz file or the one it
        has cannot be read.
    """

    for xyz_path in DirectoryScan(point_path).files(XYZ):
        try:
            return XYZ(xyz_path).atoms
        except Exception:
            continue

    return None


def geometries_match(
    one: Atoms, other: Atoms, tolerance: float = GEOMETRY_TOLERANCE
) -> bool:
    """Whether two geometries are the same geometry.

    Both are moved onto their centroid before they are compared, because the geometries
    which are written into a set are commonly centred (see ``Trajectory.to_dir``) while
    the ones in the trajectory they came from are not, and a geometry which has been
    moved is still the same geometry.

    :param one: A geometry.
    :param other: The geometry to compare it against.
    :param tolerance: How far apart the two can be, in Angstroms, and still be the same
        geometry, defaults to :data:`GEOMETRY_TOLERANCE`.
    """

    if one.atom_names != other.atom_names:
        return False

    difference = (one.coordinates - one.centroid) - (other.coordinates - other.centroid)

    return bool(np.max(np.abs(difference)) <= tolerance)


def matching_geometries(
    point_paths: Sequence[Path],
    trajectory_path: Union[str, Path],
    every: int = 1,
    nsamples: int = DEFAULT_NSAMPLES,
) -> Tuple[int, int]:
    """Checks a trajectory against the points of a set which are still there, to see
    whether it is the trajectory the set was made from.

    The geometry of a point which is missing is taken out of the trajectory by its
    position, so a trajectory which is not the one the set was made from (or which has
    had geometries taken out of it since) would quietly fill the holes in the set with
    the wrong geometries. Comparing the points which are there against the geometries the
    trajectory has at their positions is what rules that out.

    :param point_paths: The paths of the point directories which are there. A handful of
        them, spread over the set, are the ones which are compared.
    :param trajectory_path: Path of the trajectory (.xyz) file the set was made from.
    :param every: How many geometries of the trajectory each point steps over, defaults
        to 1.
    :param nsamples: How many points to compare, defaults to :data:`DEFAULT_NSAMPLES`.
    :return: How many points could be compared at all (i.e. their geometry could be read
        and the trajectory has a geometry at their position), and how many of those are
        the geometry the trajectory has at their position.
    """

    point_paths = list(point_paths)
    if not point_paths:
        return 0, 0

    # points spread over the whole set rather than the first few of it, so that a
    # trajectory which lines up at the start but not later on is not taken for the one
    step = max(1, len(point_paths) // nsamples)
    sampled_paths = point_paths[::step][:nsamples]

    geometries_by_index = {}
    for point_path in sampled_paths:

        point_name = parse_point_name(point_path.name)
        if point_name is None:
            continue

        atoms = point_geometry(point_path)
        # a point whose geometry cannot be read says nothing either way
        if atoms is not None:
            geometries_by_index[point_name.index] = atoms

    if not geometries_by_index:
        return 0, 0

    trajectory_geometries = read_geometries_from_xyz(
        trajectory_path, (index * every for index in geometries_by_index)
    )

    ncompared = 0
    nmatched = 0
    for index, geometry in geometries_by_index.items():

        trajectory_geometry = trajectory_geometries.get(index * every)
        if trajectory_geometry is None:
            continue

        ncompared += 1
        if geometries_match(geometry, trajectory_geometry):
            nmatched += 1

    return ncompared, nmatched


def points_are_centred(
    point_paths: Sequence[Path],
    nsamples: int = DEFAULT_NSAMPLES,
    tolerance: float = GEOMETRY_TOLERANCE,
) -> bool:
    """Whether the geometries of a set were centred on their centroid when it was made.

    A set is commonly (but not always) written out centred, so that the molecule does not
    wander off in space over the course of a trajectory, and a point which is made again
    should be made the same way as the rest of the set it is going into.

    :param point_paths: The paths of the point directories which are there.
    :param nsamples: How many points to look at, defaults to :data:`DEFAULT_NSAMPLES`.
    :param tolerance: How far from the origin the centroid of a geometry can be and still
        count as centred, in Angstroms.
    :return: True if every geometry which could be read sits on its centroid, False if
        any of them does not or if none of them could be read.
    """

    point_paths = list(point_paths)
    if not point_paths:
        return False

    step = max(1, len(point_paths) // nsamples)

    nread = 0
    for point_path in point_paths[::step][:nsamples]:

        atoms = point_geometry(point_path)
        if atoms is None:
            continue

        nread += 1
        if np.max(np.abs(atoms.centroid)) > tolerance:
            return False

    return nread > 0


def restore_missing_points(
    missing_points: Sequence[MissingPoint],
    trajectory_path: Union[str, Path],
    every: int = 1,
    centre: bool = True,
) -> Tuple[List[Path], List[MissingPoint]]:
    """Makes the point directories of the points which are missing from a set again, with
    their geometry taken out of the trajectory the set was made from.

    Each one is written exactly as it was written the first time round: a point directory
    named after the point, holding one .xyz file of the geometry, which is what the
    Gaussian submission writes a .gjf from.

    :param missing_points: The points to make again, as found by
        :class:`MissingPointsCheck`.
    :param trajectory_path: Path of the trajectory (.xyz) file the set was made from.
    :param every: How many geometries of the trajectory each point steps over, defaults
        to 1.
    :param centre: Whether to move each geometry onto its centroid, as ``to_dir`` does
        when a set is made, defaults to True. This should be what the rest of the set was
        made with (see :func:`points_are_centred`).
    :return: The paths of the point directories which were made, and the points which
        could not be made because the trajectory has no geometry at their position.
    """

    missing_points = list(missing_points)

    geometries = read_geometries_from_xyz(
        trajectory_path, (point.index * every for point in missing_points)
    )

    restored_paths = []
    not_in_trajectory = []

    for point in missing_points:

        atoms = geometries.get(point.index * every)
        if atoms is None:
            not_in_trajectory.append(point)
            continue

        if centre:
            atoms.centre()

        mkdir(point.path)
        XYZ(point.path / (point.name + XYZ.get_filetype()), atoms).write()
        restored_paths.append(point.path)

    return restored_paths, not_in_trajectory
