from pathlib import Path
from typing import List, Optional

from ichor.core.analysis.get_atoms import (
    get_atoms_from_path,
    get_trajectory_from_path,
)
from ichor.core.analysis.get_input import get_files_in_cwd
from ichor.core.analysis.get_path import get_path
from ichor.core.atoms import Atoms
from ichor.core.files import XYZ
from ichor.core.menu import (
    Menu,
    MenuVar,
    return_arg,
    select_multiple_from_list,
    toggle_bool_var,
)
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    ICHORCommand,
    SubmissionScript,
)


def _get_input_file() -> Path:
    files = get_files_in_cwd([XYZ.filetype])
    if len(files) == 1:
        return files[0]
    elif len(files) > 1:
        menu = Menu("Select Input File")
        for i, f in enumerate(files):
            menu.add_option(
                f"{i+1}",
                f"{f}",
                return_arg,
                args=[f],
                auto_close=True,
            )
        return menu.run()
    else:
        return _get_custom_input_file()


def _get_custom_input_file() -> Path:
    return get_path(prompt="Input File Location: ")


def _set_input_file(
    input_file: MenuVar[Path],
    output_file: MenuVar[Path],
    input_file_set: MenuVar[bool],
    output_file_set: MenuVar[bool],
    atoms: MenuVar[List[str]],
    centre_atoms: MenuVar[List[str]],
    rmsd_subsystem: MenuVar[List[str]],
):
    if not input_file_set.var:
        input_file.var = _get_input_file()
        input_file_set.var = True
    else:
        input_file.var = _get_custom_input_file()

    if not output_file_set.var:
        output_file.var = Path(
            input_file.var.parent
            / f"{input_file.var.stem}_ROTATED{XYZ.filetype}"
        )

    atoms.var = get_atoms_from_path(input_file.var).names
    centre_atoms.var = atoms.var
    rmsd_subsystem.var = atoms.var


def _set_output_file(
    output_file: MenuVar[Path], output_file_set: MenuVar[bool]
):
    output_file.var = get_path(prompt="Output File Location: ")
    output_file_set.var = True


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
                func_args=list(
                    map(str, [input_file, output_file, centre_atoms, subsys])
                ),
            )
        )
    return submission_script.submit()


def run_rotate_mol(
    input_file: Path,
    output_file: Optional[Path] = None,
    centre_atoms: Optional[List[str]] = None,
    subsys: Optional[List[str]] = None,
    submit: bool = False,
):
    if submit:
        submit_rotate_mol(input_file, output_file, centre_atoms, subsys)
    else:
        rotate_mol(input_file, output_file, centre_atoms, subsys)


def rotate_mol_menu():
    input_file_set = MenuVar("Input File Set", False)
    output_file_set = MenuVar("Output File Set", False)

    input_file = MenuVar("Input File", Path())
    output_file = MenuVar("Output File", Path())
    atoms = MenuVar("Atoms", Atoms().names)
    centre_atoms = MenuVar("Centre Atoms", atoms.var)
    rmsd_subsystem = MenuVar("RMSD Subsystem", atoms.var)

    _set_input_file(
        input_file,
        output_file,
        input_file_set,
        output_file_set,
        atoms,
        centre_atoms,
        rmsd_subsystem,
    )

    submit = MenuVar("Submit", False)

    with Menu("Rotate-Mol Menu") as menu:
        menu.add_option(
            "1",
            "Run rotate-mol",
            run_rotate_mol,
            kwargs={
                "input_file": input_file,
                "output_file": output_file,
                "centre_atoms": centre_atoms,
                "subsys": rmsd_subsystem,
                "submit": submit,
            },
        )
        menu.add_space()
        menu.add_option(
            "c",
            "Edit Centre Atom(s)",
            select_multiple_from_list,
            args=[atoms, centre_atoms, "Select Atoms To Centre On"],
        )
        menu.add_option(
            "s",
            "Edit RMSD Subsystem",
            select_multiple_from_list,
            args=[atoms, rmsd_subsystem, "Select Atoms Use as Subsystem"],
        )
        menu.add_space()
        menu.add_option(
            "i",
            "Set Input File",
            _set_input_file,
            args=[
                input_file,
                output_file,
                input_file_set,
                output_file_set,
                atoms,
                centre_atoms,
                rmsd_subsystem,
            ],
        )
        menu.add_option(
            "o", "Set Output File", _set_output_file, args=[output_file]
        )
        menu.add_space()
        menu.add_option(
            "submit", "Toggle Submit", toggle_bool_var, args=[submit]
        )
        menu.add_space()
        menu.add_var(centre_atoms)
        menu.add_var(rmsd_subsystem)
        menu.add_space()
        menu.add_var(input_file)
        menu.add_var(output_file)
        menu.add_space()
        menu.add_var(submit)
