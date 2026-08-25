"""Tests for finding the points which have gone missing from a PointsDirectory and
making them again from the trajectory the set was written out of.

A set is made from a trajectory the way one is made in practice, point directories are
deleted from it the way an accidental deletion does, and the missing points are asserted
to be found and to be put back with the geometries they had.
"""

import shutil

import numpy as np
import pytest
from ichor.core.atoms import Atom, Atoms
from ichor.core.files import PointsDirectory, Trajectory, XYZ
from ichor.core.processing.missing_points import (
    geometries_match,
    matching_geometries,
    MissingPointsCheck,
    parse_point_name,
    point_geometry,
    points_are_centred,
    restore_missing_points,
)

NGEOMETRIES = 12
SYSTEM_NAME = "WATER"


def water(offset: float) -> Atoms:
    """A water geometry which is a little different from every other one, so that two
    geometries of the trajectory are never mistaken for each other."""

    atoms = Atoms()
    atoms.add(Atom("O", 0.0, 0.0, offset))
    atoms.add(Atom("H", 0.758602, 0.0, 0.504284 + offset))
    atoms.add(Atom("H", 0.260455, 0.0, -0.872893 - offset))

    return atoms


@pytest.fixture
def trajectory_path(tmp_path):
    """A trajectory of geometries which are all slightly different from each other."""

    trajectory = Trajectory(tmp_path / "trajectory.xyz")
    for i in range(NGEOMETRIES):
        trajectory.add(water(0.01 * i))
    trajectory.write()

    return trajectory.path


@pytest.fixture
def points_directory(tmp_path, trajectory_path):
    """A PointsDirectory made from that trajectory, one point per geometry, as the
    trajectory splitting menu makes one."""

    points_directory_path = Trajectory(trajectory_path).to_dir(
        SYSTEM_NAME, parent_dir=tmp_path
    )
    # the geometries are written out as loose .xyz files, which reading the set as a
    # PointsDirectory turns into point directories
    PointsDirectory(points_directory_path)

    return points_directory_path


def point_names(points_directory_path):
    """The names of the point directories which are on disk, in order."""
    return sorted(p.name for p in points_directory_path.iterdir() if p.is_dir())


def delete_points(points_directory_path, *indices):
    """Deletes point directories from a set, as an accidental deletion does."""

    for index in indices:
        shutil.rmtree(points_directory_path / f"{SYSTEM_NAME}{index:04d}.pointdir")


def test_parse_point_name():

    assert parse_point_name("WATER0143") == parse_point_name("WATER0143.pointdir")

    parsed = parse_point_name("WATER_MONOMER0143.pointdir")
    assert parsed.system_name == "WATER_MONOMER"
    assert parsed.index == 143
    assert parsed.width == 4
    assert parsed.name_of(7) == "WATER_MONOMER0007"

    # a directory which is not named after a geometry of a trajectory says nothing about
    # where it belongs in a sequence
    assert parse_point_name("SOME_DIRECTORY") is None


def test_nothing_is_missing_from_a_complete_set(points_directory, trajectory_path):

    check = MissingPointsCheck(points_directory, ngeometries=NGEOMETRIES)

    assert check.npresent == NGEOMETRIES
    assert check.nmissing == 0
    assert len(check.sequences) == 1
    assert check.sequences[0].system_name == SYSTEM_NAME
    assert check.sequences[0].stride == 1


def test_points_deleted_from_the_middle_are_found(points_directory):

    delete_points(points_directory, 3, 4, 9)

    # the holes between the points which are there are found without the trajectory
    check = MissingPointsCheck(points_directory)

    assert check.nmissing == 3
    assert [point.index for point in check.missing] == [3, 4, 9]
    assert [point.name for point in check.missing] == [
        "WATER0003",
        "WATER0004",
        "WATER0009",
    ]
    assert all(point.points_directory == points_directory for point in check.missing)


def test_points_deleted_from_the_end_are_only_found_with_the_trajectory(
    points_directory,
):

    delete_points(points_directory, NGEOMETRIES - 2, NGEOMETRIES - 1)

    # the set is complete as far as its own names go, so the last geometry of it could
    # just as well be the last geometry it was ever made with
    assert MissingPointsCheck(points_directory).nmissing == 0

    # the trajectory says how far the sequence should have gone
    check = MissingPointsCheck(points_directory, ngeometries=NGEOMETRIES)
    assert [point.index for point in check.missing] == [
        NGEOMETRIES - 2,
        NGEOMETRIES - 1,
    ]


def test_a_set_of_every_nth_geometry_keeps_its_stride(tmp_path, trajectory_path):
    """A set made of every third geometry is numbered 0000, 0003, 0006..., so the gaps
    between its points are the way it was made rather than points which are missing."""

    points_directory = Trajectory(trajectory_path).to_dir(
        SYSTEM_NAME, every=3, parent_dir=tmp_path
    )
    PointsDirectory(points_directory)

    assert MissingPointsCheck(points_directory).nmissing == 0
    assert MissingPointsCheck(points_directory).sequences[0].stride == 3

    delete_points(points_directory, 6)

    check = MissingPointsCheck(points_directory)
    assert [point.index for point in check.missing] == [6]


def test_missing_points_are_restored_with_their_own_geometries(
    points_directory, trajectory_path
):

    delete_points(points_directory, 2, 7)

    check = MissingPointsCheck(points_directory, ngeometries=NGEOMETRIES)
    restored_paths, not_in_trajectory = restore_missing_points(
        check.missing, trajectory_path, centre=False
    )

    assert not not_in_trajectory
    assert len(restored_paths) == 2
    # the set is whole again, and the points which were put back are named and ordered
    # exactly as the ones which were never deleted
    assert point_names(points_directory) == [
        f"{SYSTEM_NAME}{i:04d}.pointdir" for i in range(NGEOMETRIES)
    ]
    assert MissingPointsCheck(points_directory, ngeometries=NGEOMETRIES).nmissing == 0

    trajectory = Trajectory(trajectory_path)
    for index, path in zip((2, 7), restored_paths):
        restored = point_geometry(path)
        assert restored is not None
        assert geometries_match(restored, trajectory[index])
        # the geometry of the point which was put back is the geometry of the point which
        # was deleted, not merely one which is like it
        assert np.allclose(restored.coordinates, trajectory[index].coordinates)


def test_restoring_centres_the_geometries_when_asked(points_directory, trajectory_path):
    """A point which is made again should be made the same way as the rest of the set it
    is going into, i.e. centred if the set was written out centred."""

    delete_points(points_directory, 5)

    check = MissingPointsCheck(points_directory)
    restored_paths, _ = restore_missing_points(
        check.missing, trajectory_path, centre=True
    )

    restored = point_geometry(restored_paths[0])
    assert np.max(np.abs(restored.centroid)) < 1e-8
    # centring moves a geometry without changing it
    assert geometries_match(restored, Trajectory(trajectory_path)[5])


def test_points_are_centred_says_how_the_set_was_written_out(
    tmp_path, trajectory_path, points_directory
):

    assert not points_are_centred(list(points_directory.iterdir()))

    centred_points_directory = Trajectory(trajectory_path).to_dir(
        "CENTRED", center=True, parent_dir=tmp_path / "centred"
    )
    PointsDirectory(centred_points_directory)

    assert points_are_centred(list(centred_points_directory.iterdir()))


def test_a_trajectory_is_checked_against_the_points_which_are_there(
    tmp_path, points_directory, trajectory_path
):

    point_paths = MissingPointsCheck(points_directory).present_point_paths
    assert len(point_paths) == NGEOMETRIES
    assert all(path.is_dir() for path in point_paths)

    ncompared, nmatched = matching_geometries(point_paths, trajectory_path)
    assert ncompared == nmatched > 0

    # a trajectory of the same system whose geometries are in a different order is not
    # the trajectory this set was made from, and filling the holes of the set from it
    # would put the wrong geometries in them
    other_trajectory = Trajectory(tmp_path / "other.xyz")
    for i in reversed(range(NGEOMETRIES)):
        other_trajectory.add(water(0.01 * i))
    other_trajectory.write()

    ncompared, nmatched = matching_geometries(point_paths, other_trajectory.path)
    assert ncompared > 0
    assert nmatched < ncompared


def test_points_past_the_end_of_the_trajectory_are_not_restored(
    points_directory, trajectory_path
):
    """A trajectory which is shorter than the set says it should be cannot give back
    every point, and the ones it cannot are reported rather than quietly skipped."""

    delete_points(points_directory, 4)

    short_trajectory = Trajectory(trajectory_path.with_name("short.xyz"))
    for i in range(3):
        short_trajectory.add(water(0.01 * i))
    short_trajectory.write()

    check = MissingPointsCheck(points_directory)
    restored_paths, not_in_trajectory = restore_missing_points(
        check.missing, short_trajectory.path
    )

    assert not restored_paths
    assert [point.index for point in not_in_trajectory] == [4]


def test_directories_which_are_not_named_after_a_geometry_are_left_alone(
    points_directory,
):

    (points_directory / "SOME_OTHER_DIRECTORY.pointdir").mkdir()

    check = MissingPointsCheck(points_directory)

    assert check.nmissing == 0
    assert [p.name for p in check.unnamed_points] == ["SOME_OTHER_DIRECTORY.pointdir"]


def test_a_missing_point_knows_which_points_directory_it_belongs_in(tmp_path):
    """A trajectory which was split into chunks numbers its points across the chunks, so
    a point which is missing belongs in the chunk which holds the points around it."""

    trajectory = Trajectory(tmp_path / "chunked.xyz")
    for i in range(NGEOMETRIES):
        trajectory.add(water(0.01 * i))
    trajectory.write()

    parent_path = trajectory.to_dirs(
        SYSTEM_NAME, split_size=4, parent_dir=tmp_path / "chunks"
    )
    for points_directory_path in parent_path.iterdir():
        PointsDirectory(points_directory_path)

    # one point out of the middle chunk of the three
    shutil.rmtree(
        parent_path / f"{SYSTEM_NAME}1.pointsdir" / f"{SYSTEM_NAME}0005.pointdir"
    )

    check = MissingPointsCheck(parent_path)

    assert check.nmissing == 1
    # the chunks are one sequence, as the points are numbered across them
    assert len(check.sequences) == 1
    assert check.missing[0].index == 5
    assert check.missing[0].points_directory.name == f"{SYSTEM_NAME}1.pointsdir"


def test_restoring_writes_a_point_directory_the_submission_can_use(
    points_directory, trajectory_path
):
    """A point which was put back holds an .xyz file named after it, which is what the
    Gaussian submission writes a .gjf from."""

    delete_points(points_directory, 6)

    check = MissingPointsCheck(points_directory)
    restored_paths, _ = restore_missing_points(check.missing, trajectory_path)

    restored_path = restored_paths[0]
    assert restored_path.name == f"{SYSTEM_NAME}0006.pointdir"
    assert [f.name for f in restored_path.iterdir()] == [f"{SYSTEM_NAME}0006.xyz"]
    assert XYZ(restored_path / f"{SYSTEM_NAME}0006.xyz").atoms.names == [
        "O1",
        "H2",
        "H3",
    ]
