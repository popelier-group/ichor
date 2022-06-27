from ichor.core.atoms import Atoms, Atom
from ichor.core.files import XYZ

def _test_write_xyz(xyz_file, xyz_file_contents): 

    assert xyz_file.path.read_text() == xyz_file_contents

def test_xyz(tmp_path):

    d = tmp_path / "xyz"
    d.mkdir()
    xyz_file_path = d / "water_dimer.xyz"

    atoms = Atoms(
        [
            Atom(
                "O",
                0.0000000000000000000,
                0.00000000000000000,
                0.00000000000000000,
            ),
            Atom(
                "H",
                -0.5350658173492745000,
                -0.96513545593593150,
                0.34177238995479650,
            ),
            Atom(
                "H",
                0.9912520884083418000,
                0.11847125457966462,
                -0.04195287155767175,
            ),
            Atom(
                "O",
                -6.243578624055563e-17,
                0.00000000000000000,
                -3.30362878833371450,
            ),
            Atom(
                "H",
                0.0000000000000000000,
                0.33294582772684770,
                -4.26739270395095400,
            ),
            Atom(
                "H",
                -6.180093092917877e-17,
                -0.93417428703609300,
                -3.63732168743662680,
            ),
        ]
    )

    xyz_file = XYZ(xyz_file_path, atoms=atoms)
    xyz_file.write()

    xyz_file_contents = "6\n\nO   0.00000000   0.00000000   0.00000000\nH  -0.53506582  -0.96513546   0.34177239\nH   0.99125209   0.11847125  -0.04195287\nO  -0.00000000   0.00000000  -3.30362879\nH   0.00000000   0.33294583  -4.26739270\nH  -0.00000000  -0.93417429  -3.63732169\n"

    _test_write_xyz(xyz_file, xyz_file_contents)