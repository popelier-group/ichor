from pathlib import Path
from typing import List, Optional

from ichor.cli.menus.menu import Menu
from ichor.cli.menus.tab_completer import ListCompleter
from ichor.core.analysis.get_atoms import (
    get_atoms_from_path,
    get_trajectory_from_path,
)
from ichor.core.analysis.get_input import get_files_in_cwd
from ichor.core.analysis.get_path import get_path
from ichor.core.atoms import Atoms
from ichor.core.files import XYZ, PointsDirectory, Trajectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    ICHORCommand,
    SubmissionScript,
)

_traj: Optional[Trajectory] = None
_atoms: Optional[Atoms] = None

_centre_atoms: List[str] = []
_rmsd_subsystem: List[str] = []

_input_file: Optional[Path] = None
_output_file: Optional[Path] = None
_output_file_set: bool = False

_submit = False


def _first_ts_of_input() -> Atoms:
    return get_atoms_from_path(_input_file)


def _find_default_file():
    files = get_files_in_cwd([XYZ.filetype])
    if len(files) == 1:
        _set_input_file(files[0])
    elif len(files) > 1:
        with Menu("Select Input File") as menu:
            for i, f in enumerate(files):
                menu.add_option(
                    f"{i+1}",
                    f"{f}",
                    _set_input_file,
                    kwargs={"input_file": f},
                    auto_close=True,
                )
    else:
        _set_input_file()


def _set_input_file(input_file: Optional[Path] = None) -> Path:
    global _input_file
    global _output_file
    global _atoms
    global _centre_atoms
    global _rmsd_subsystem
    _input_file = input_file or _get_input_file()
    if not _output_file_set:
        _output_file = Path(
            _input_file.parent / f"{_input_file.stem}_ROTATED{XYZ.filetype}"
        )

    _atoms = _first_ts_of_input()
    _centre_atoms = _atoms.names
    _rmsd_subsystem = _atoms.names
    return _input_file


def _set_output_file():
    global _output_file
    global _output_file_set
    _output_file = get_path(prompt="Output File Location: ")
    _output_file_set = True


def _get_input_file() -> Path:
    return get_path(prompt="Input File Location: ")


def _set_centre_atoms():
    global _centre_atoms
    _centre_atoms = []

    def toggle_centre_atom(atom: str):
        global _centre_atoms
        if atom in _centre_atoms:
            del _centre_atoms[_centre_atoms.index(atom)]
        else:
            _centre_atoms += [atom]

    while True:
        Menu.clear_screen()
        print("Select Atoms To Centre On")
        _all_atoms = _atoms.names
        with ListCompleter(_all_atoms + ["all", "c", "clear"]):
            for atom_name in _all_atoms:
                print(
                    f"[{'x' if atom_name in _centre_atoms else ' '}] {atom_name}"
                )
            print()
            ans = input(">> ")
            ans = ans.strip()
            if ans == "":
                break
            elif ans in _all_atoms:
                toggle_centre_atom(ans)
            elif ans == "all":
                _centre_atoms = list(_all_atoms)
            elif ans in ["c", "clear"]:
                _centre_atoms.clear()


def _set_subsys_atoms():
    global _rmsd_subsystem
    _rmsd_subsystem = []

    def toggle_subsys_atom(atom: str):
        global _rmsd_subsystem
        if atom in _rmsd_subsystem:
            del _rmsd_subsystem[_rmsd_subsystem.index(atom)]
        else:
            _rmsd_subsystem += [atom]

    while True:
        Menu.clear_screen()
        print("Select Atoms Use as Subsystem")
        _all_atoms = _atoms.names
        with ListCompleter(_all_atoms + ["all", "c", "clear"]):
            for atom_name in _all_atoms:
                print(
                    f"[{'x' if atom_name in _rmsd_subsystem else ' '}] {atom_name}"
                )
            print()
            ans = input(">> ")
            ans = ans.strip()
            if ans == "":
                break
            elif ans in _all_atoms:
                toggle_subsys_atom(ans)
            elif ans == "all":
                _rmsd_subsystem = list(_all_atoms)
            elif ans in ["c", "clear"]:
                _rmsd_subsystem.clear()


def rotate_mol(
    input_file: Path,
    output_file: Optional[Path] = None,
    centre_atoms: Optional[List[str]] = None,
    subsys: Optional[List[str]] = None,
):
    trajectory = get_trajectory_from_path(input_file)

    if output_file is None:
        output_file = Path("rotated-output.xyz")
    if centre_atoms is None:
        centre_atoms = trajectory.atom_names
    if subsys is None:
        subsys = trajectory.atom_names

    for point in trajectory:
        point.centre()

    i = 0
    for point in trajectory:
        R = trajectory[0][subsys].kabsch(point[subsys])
        point.rotate(R)
        i += 50

    for point in trajectory:
        point.centre(centre_atoms)

    trajectory.write(output_file)


def submit_rotate_mol(
    input_file: Path,
    output_file: Optional[Path] = None,
    centre_atoms: Optional[List[str]] = None,
    subsys: Optional[List[str]] = None,
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["analysis"]["rotate-mol"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="rotate_mol",
                func_args=[input_file, output_file, centre_atoms, subsys],
            )
        )
    return submission_script.submit()


def run_rotate_mol(
    input_file: Path,
    output_file: Optional[Path] = None,
    centre_atoms: Optional[List[str]] = None,
    subsys: Optional[List[str]] = None,
):
    if _submit:
        submit_rotate_mol(input_file, output_file, centre_atoms, subsys)
    else:
        rotate_mol(input_file, output_file, centre_atoms, subsys)


def _toggle_submit():
    global _submit
    _submit = not _submit


def _rotate_mol_menu_refresh(menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Run rotate-mol",
        run_rotate_mol,
        kwargs={
            "input_file": _input_file,
            "output_file": _output_file,
            "centre_atoms": _centre_atoms,
            "subsys": _rmsd_subsystem,
        },
    )
    menu.add_space()
    menu.add_option("c", "Edit Centre Atom(s)", _set_centre_atoms)
    menu.add_option("s", "Edit RMSD Subsystem", _set_subsys_atoms)
    menu.add_space()
    menu.add_option("i", "Set Input File", _set_input_file)
    menu.add_option("o", "Set Output File", _set_output_file)
    menu.add_space()
    menu.add_option("submit", "Toggle Submit", _toggle_submit)
    menu.add_space()
    menu.add_message(f"Centre Atom(s): {_centre_atoms}")
    menu.add_message(f"RMSD Subsystem: {_rmsd_subsystem}")
    menu.add_space()
    menu.add_message(f"Input File: {_input_file}")
    menu.add_message(f"Output File: {_output_file}")
    menu.add_space()
    menu.add_message(f"Submit: {_submit}")
    menu.add_final_options()


def rotate_mol_menu():
    _find_default_file()
    with Menu("Rotate-Mol Menu", refresh=_rotate_mol_menu_refresh):
        pass
