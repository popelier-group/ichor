from ichor.core.files import GJF
from ichor.core.atoms import Atoms, Atom

# TODO: the wfn path that is written to file is relative, so cannot have that part in the gjfs (as tmp directory path is random)

def _test_write_gjf(gjf_file, gjf_file_contents): 

    assert gjf_file.path.read_text() == gjf_file_contents

def test_one_atom(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm\n\ntest\n\n0   1\nO   1.00000000   2.00000000   3.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, title="test", keywords=["nosymm"])
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)


def test_multiple_atoms(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm\n\ntest\n\n0   1\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, title="test", keywords=["nosymm"])
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)

def test_multiple_keywords(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm opt freq\n\ntest\n\n0   1\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, title="test", keywords=["nosymm", "opt", "freq"])
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)

def test_charge(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm\n\ntest\n\n5   1\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, title="test", keywords=["nosymm"], charge=5)
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)

def test_spin_multiplicity(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p b3lyp/6-31+g(d,p) nosymm\n\ntest\n\n5   10\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, title="test", keywords=["nosymm"], charge=5, spin_multiplicity=10)
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)

def test_basis_set(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p b3lyp/aug-cc-pvtz nosymm\n\ntest\n\n5   10\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, basis_set="aug-cc-pvtz", title="test", keywords=["nosymm"], charge=5, spin_multiplicity=10)
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)

def test_method(tmp_path):

    d = tmp_path / "gjf"
    d.mkdir()
    gjf_file_path = d / "simple_gjf.gjf"

    atoms = Atoms()
    atoms.append(Atom("O", 1.0, 2.0, 3.0))
    atoms.append(Atom("H", 2.0, 3.0, 4.0))
    atoms.append(Atom("H", 5.0, 6.0, 7.0))

    gjf_file_contents = "#p mp2/6-31+g(d,p) nosymm\n\ntest\n\n5   10\nO   1.00000000   2.00000000   3.00000000\nH   2.00000000   3.00000000   4.00000000\nH   5.00000000   6.00000000   7.00000000\n"

    gjf_file = GJF(gjf_file_path, atoms=atoms, method="mp2", title="test", keywords=["nosymm"], charge=5, spin_multiplicity=10)
    gjf_file.write()

    _test_write_gjf(gjf_file, gjf_file_contents)
