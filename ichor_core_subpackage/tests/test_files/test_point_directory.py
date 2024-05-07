from pathlib import Path

from ichor.core.files import PointDirectory

from tests.path import get_cwd

example_dir = (
    get_cwd(__file__)
    / ".."
    / ".."
    / ".."
    / "example_files"
    / "example_points_directory"
    / "WATER_MONOMER.pointsdir"
    / "WATER_MONOMER0000.pointdir"
)


def _test_point_directory(
    point_dir_path=Path,
):

    point_dir_inst = PointDirectory(point_dir_path)

    gjf_path = point_dir_inst.gjf.path
    gaussian_out_path = point_dir_inst.gaussian_output.path
    xyz_inst = point_dir_inst.xyz.path
    ints_path = point_dir_inst.ints.path
    aim_path = point_dir_inst.aim.path
    wfn_path = point_dir_inst.wfn.path

    # check that each file/dir type can be accessed as an attribute
    # by the contents class variable
    assert gjf_path.exists() is True
    assert gaussian_out_path.exists() is True
    assert xyz_inst.exists() is True
    assert ints_path.exists() is True
    assert aim_path.exists() is True
    assert wfn_path.exists() is True


def test_water_monomer_point_directory1():

    _test_point_directory(example_dir)
