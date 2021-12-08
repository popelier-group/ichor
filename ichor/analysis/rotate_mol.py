from ichor.menu import Menu
from ichor.files import XYZ, Trajectory, PointsDirectory
from ichor.analysis.get_path import get_path
from ichor.analysis.get_input import get_files_in_cwd
# from ichor.analysis
from pathlib import Path
from typing import Optional

_traj = []
_atoms = None

_centre_atoms = []
_rmsd_subsystem = []

_input_file = None
_output_file = None
_output_file_set = False


def _first_ts_of_input():



def _find_default_file() -> Path:
    files = get_files_in_cwd([XYZ.filetype])
    if len(files) == 1:
        _set_input_file(files[0])
    elif len(files) > 1:
        with Menu("Select Input File") as menu:
            for i, f in enumerate(files):
                menu.add_option(f"{i+1}", f"{f}", _set_input_file, kwargs={"input_file": f})
    else:
        _set_input_file()


def _set_input_file(input_file: Optional[Path] = None) -> Path:
    global _input_file
    global _output_file
    _input_file = input_file if input_file is None else _get_input_file()
    if not _output_file_set:
        _output_file = Path(_input_file.parent / (_input_file.stem + "_ROTATED" + XYZ.filetype))
    return _input_file


def _set_output_file():
    global _output_file
    global _output_file_set
    _output_file = get_path(prompt="Output File Location: ")
    _output_file_set = True


def _get_input_file() -> Path:
    return get_path(prompt="Input File Location: ")


def _rotate_mol_menu_refresh(menu):
    menu.clear_options()
    menu.add_option("1" "Run rotate-mol")
    menu.add_space()
    menu.add_option("c", "Edit Centre Atom(s)")
    menu.add_option("s", "Edit RMSD Subsystem")
    menu.add_space()
    menu.add_option("i", "Set Input File", _set_input_file)
    menu.add_option("o", "Set Output File", _set_output_file)
    menu.add_space()
    menu.add_option(f"Centre Atom(s): {_centre_atoms}")
    menu.add_option(f"RMSD Subsystem: {_rmsd_subsystem}")


def rotate_mol_menu():
    _find_default_file()
    with Menu("Rotate-Mol Menu", refresh=_rotate_mol_menu_refresh):
        pass
