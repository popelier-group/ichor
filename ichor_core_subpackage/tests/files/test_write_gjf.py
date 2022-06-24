from ichor.core.files import GJF
from ichor.core.atoms import Atoms, Atom

def _test_write_gjf(gjf_file, gjf_file_contents): 

    assert gjf_file.path.read_text() == gjf_file_contents


def test_simple_gjf(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm\n\ntest\n\n0   1\nO   1.00000000   2.00000000   3.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, comment_line="test", keywords=["nosymm"])
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)
