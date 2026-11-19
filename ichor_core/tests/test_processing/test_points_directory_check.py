"""Tests for the Gaussian and AIMAll checks of a PointsDirectory.

A copy of the example PointsDirectory (in which every point is finished) is broken in
the ways a real calculation fails, i.e. output which was never written and output which
was cut short, and the checks are asserted to find exactly those points.
"""

import shutil

import pytest
from ichor.core.common.units import AtomicDistance
from ichor.core.files import GJF, PointDirectory, WFX
from ichor.core.processing.points_directory_check import (
    AimallCheck,
    GaussianCheck,
    INCOMPLETE,
    MISSING,
    OK,
    wfx_is_finished,
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


# A small stand-in for Gaussian output, with packed numbers and a Fortran exponent.
WFX_TEXT = """<Title>
Water
</Title>
<Number of Nuclei>
3
</Number of Nuclei>
<Number of Primitives>
21
</Number of Primitives>
<Number of Occupied Molecular Orbitals>
5
</Number of Occupied Molecular Orbitals>
<Atomic Numbers>
8 1 1
</Atomic Numbers>
<Nuclear Cartesian Coordinates>
0 0 0
1.4D+00 0 1
-1.4D+00 0 1
</Nuclear Cartesian Coordinates>
<Energy = T + Vne + Vee + Vnn>
-76.5
</Energy = T + Vne + Vee + Vnn>
<Virial Ratio (-V/T)>
2.0
</Virial Ratio (-V/T)>
"""


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

    for point in copied_points_directory.glob("*.pointdir"):
        (point / f"{point.stem}.wfx").write_text(WFX_TEXT)

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


def test_gaussian_check_finds_missing_and_truncated_wfxs(points_directory):

    # a point Gaussian has not run on (or which crashed before writing anything)
    (points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfx").unlink()
    # a point whose Gaussian job was killed part way through writing the wavefunction
    truncate(points_directory / "WATER_MONOMER0002.pointdir" / "WATER_MONOMER0002.wfx")

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


def test_gaussian_check_ignores_truncated_wfxs_if_not_checking_contents(
    points_directory,
):

    truncate(points_directory / "WATER_MONOMER0002.pointdir" / "WATER_MONOMER0002.wfx")

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


def test_wfx_is_finished(points_directory, tmp_path):
    """A wavefunction is only usable (by AIMAll, or as a finished point) if Gaussian
    wrote its metadata and closed its sections."""

    finished_wfx = (
        points_directory / "WATER_MONOMER0000.pointdir" / "WATER_MONOMER0000.wfx"
    )
    truncated_wfx = (
        points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfx"
    )
    truncate(truncated_wfx)

    empty_wfx = tmp_path / "EMPTY.wfx"
    empty_wfx.touch()

    assert wfx_is_finished(finished_wfx)
    assert not wfx_is_finished(truncated_wfx)
    assert not wfx_is_finished(empty_wfx)
    assert not wfx_is_finished(tmp_path / "NOT_THERE.wfx")


def test_report_is_written_with_every_point(points_directory, tmp_path):

    (points_directory / "WATER_MONOMER0001.pointdir" / "WATER_MONOMER0001.wfx").unlink()

    check = GaussianCheck(points_directory)
    report_path = check.write_report(tmp_path / "GAUSSIAN-CHECK-REPORT.txt")
    report = report_path.read_text()

    for point_name in statuses(check):
        assert point_name in report
    assert "Points checked" in report


def test_point_directory_prefers_wfx_and_can_read_its_geometry(points_directory):
    point_path = points_directory / "WATER_MONOMER0000.pointdir"
    (point_path / f"{point_path.stem}.xyz").unlink()
    point = PointDirectory(point_path)

    assert isinstance(point.wavefunction, WFX)
    assert point.raw_data["wfx"] == {"energy": -76.5, "virial_ratio": 2.0}
    assert point.wavefunction.atoms[1].units == AtomicDistance.Bohr
    assert point.atoms[1].x == pytest.approx(0.740848, abs=1e-6)


def test_wfx_model_is_added_without_changing_the_payload(tmp_path):
    path = tmp_path / "water.wfx"
    path.write_text(WFX_TEXT)
    original = path.read_bytes()
    WFX(path).ensure_model("B3LYP")

    assert path.read_bytes().endswith(original)
    assert WFX(path).method == "B3LYP"
    WFX(path).ensure_model("PBE")
    assert WFX(path).method == "B3LYP"


@pytest.mark.parametrize("existing_model", ["", "PBE"])
def test_wfx_model_sections_are_deduplicated(tmp_path, existing_model):
    path = tmp_path / "water.wfx"
    path.write_text(
        f"<Model>\n{existing_model}\n</Model>\n{WFX_TEXT}<Model>\n\n</Model>\n"
    )

    WFX(path).ensure_model("B3LYP")

    assert path.read_text().count("<Model>") == 1
    assert WFX(path).method == (existing_model or "B3LYP")
    assert WFX_TEXT in path.read_text()


def test_existing_gaussian_input_is_migrated_without_losing_extra_sections(tmp_path):
    gjf = tmp_path / "water.gjf"
    gjf.write_text(
        "%mem=4GB\n#p B3LYP/gen\n Output=(WFN,CSGTCX)\n\n"
        "Water\n\n0 1\nO 0 0 0\n\nO 0\nSTO-3G\n****\n\nold.wfn\n"
    )

    output = GJF.prepare_wfx_output(gjf)

    assert output == gjf.with_suffix(".wfx")
    assert "Output=(wfx,CSGTCX)" in gjf.read_text()
    assert "\nO 0\nSTO-3G\n****\n\n" in gjf.read_text()
    assert gjf.read_text().endswith(f"{output}\n\n")
    updated = gjf.read_bytes()
    assert GJF.prepare_wfx_output(gjf) == output
    assert gjf.read_bytes() == updated
