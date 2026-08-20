"""Tests for the Gaussian and AIMAll checks of a PointsDirectory.

A copy of the example PointsDirectory (in which every point is finished) is broken in
the ways a real calculation fails, i.e. output which was never written and output which
was cut short, and the checks are asserted to find exactly those points.
"""

import shutil

import pytest
from ichor.core.processing.points_directory_check import (
    AimallCheck,
    GaussianCheck,
    INCOMPLETE,
    MISSING,
    OK,
    wfn_is_finished,
)

from tests.path import get_cwd

example_points_directory = (
    get_cwd(__file__)
    / ".."
    / ".."
    / ".."
    / "example_files"
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
)


def truncate(path, nlines: int = 10):
    """Cuts a file short, as a calculation which is killed part way through does."""

    with open(path, "r") as f:
        lines = [next(f) for _ in range(nlines)]

    with open(path, "w") as f:
        f.writelines(lines)


@pytest.fixture
def points_directory(tmp_path):
    """A writeable copy of the example PointsDirectory, in which every point has a
    finished wavefunction and a full set of atomic files."""

    copied_points_directory = tmp_path / example_points_directory.name
    shutil.copytree(example_points_directory, copied_points_directory)

    return copied_points_directory


def statuses(check) -> dict:
    """The status of every point of a check, by point name."""
    return {result.name: result.status for result in check.results}


def test_finished_points_directory_passes_both_checks(points_directory):

    gaussian_check = GaussianCheck(points_directory)
    aimall_check = AimallCheck(points_directory)

    assert gaussian_check.npoints == 4
    assert gaussian_check.counts[OK] == 4
    assert not gaussian_check.problem_points

    assert aimall_check.npoints == 4
    assert aimall_check.counts[OK] == 4
    assert not aimall_check.problem_points


def test_gaussian_check_finds_missing_and_truncated_wfns(points_directory):

    # a point Gaussian has not run on (or which crashed before writing anything)
    (points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfn").unlink()
    # a point whose Gaussian job was killed part way through writing the wavefunction
    truncate(points_directory / "WATER_MONOMER0002.pointdir" / "WATER_MONOMER0002.wfn")

    check = GaussianCheck(points_directory)

    assert statuses(check) == {
        "WATER_MONOMER0000.pointdir": OK,
        "WATER_MONOMER0001.pointdir": MISSING,
        "WATER_MONOMER0002.pointdir": INCOMPLETE,
        "WATER_MONOMER0003.pointdir": OK,
    }
    assert check.counts == {OK: 2, MISSING: 1, INCOMPLETE: 1}

    # only the points which need looking at are in the report of the problem points
    problem_report = check.report(include_ok=False)
    assert "WATER_MONOMER0001.pointdir" in problem_report
    assert "WATER_MONOMER0000.pointdir" not in problem_report


def test_gaussian_check_ignores_truncated_wfns_if_not_checking_contents(
    points_directory,
):

    truncate(points_directory / "WATER_MONOMER0002.pointdir" / "WATER_MONOMER0002.wfn")

    check = GaussianCheck(points_directory, check_file_contents=False)

    assert check.counts[OK] == 4


def test_aimall_check_finds_points_without_atomic_files(points_directory):

    shutil.rmtree(
        points_directory
        / "WATER_MONOMER0001.pointdir"
        / "WATER_MONOMER0001_atomicfiles"
    )

    check = AimallCheck(points_directory)
    result = {r.name: r for r in check.results}["WATER_MONOMER0001.pointdir"]

    assert result.status == MISSING
    assert "no _atomicfiles directory" in result.problems[0]


def test_aimall_check_finds_incomplete_atomic_files(points_directory):

    point = points_directory / "WATER_MONOMER0002.pointdir"
    atomic_files = point / "WATER_MONOMER0002_atomicfiles"

    # an atom which was never integrated, one which was integrated part way, and the
    # files AIMAll leaves behind when it crashes
    (atomic_files / "h3.int").unlink()
    truncate(atomic_files / "o1.int")
    (atomic_files / "h2.mog").touch()
    (point / "AIMALL.sh").touch()

    check = AimallCheck(points_directory)
    result = {r.name: r for r in check.results}["WATER_MONOMER0002.pointdir"]
    problems = "; ".join(result.problems)

    assert result.status == INCOMPLETE
    assert check.counts == {OK: 3, MISSING: 0, INCOMPLETE: 1}
    assert "no .int file for 1 of 3 atoms (H3)" in problems
    assert "O1" in problems
    assert ".mog files left for H2" in problems
    assert "AIMALL.sh" in problems


def test_wfn_is_finished(points_directory, tmp_path):
    """A wavefunction is only usable (by AIMAll, or as a finished point) if Gaussian
    wrote it all the way to its total energy line."""

    finished_wfn = (
        points_directory / "WATER_MONOMER0000.pointdir" / "WATER_MONOMER0000.wfn"
    )
    truncated_wfn = (
        points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfn"
    )
    truncate(truncated_wfn)

    empty_wfn = tmp_path / "EMPTY.wfn"
    empty_wfn.touch()

    assert wfn_is_finished(finished_wfn)
    assert not wfn_is_finished(truncated_wfn)
    assert not wfn_is_finished(empty_wfn)
    assert not wfn_is_finished(tmp_path / "NOT_THERE.wfn")


def test_report_is_written_with_every_point(points_directory, tmp_path):

    (points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfn").unlink()

    check = GaussianCheck(points_directory)
    report_path = check.write_report(tmp_path / "GAUSSIAN-CHECK-REPORT.txt")
    report = report_path.read_text()

    for point_name in statuses(check):
        assert point_name in report
    assert "Points checked" in report
