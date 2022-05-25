from pathlib import Path
from typing import Optional

from ichor.ichor_lib.analysis.get_input import get_first_file, get_input_menu
from ichor.ichor_lib.atoms import Atoms
from ichor.ichor_hpc.batch_system import JobID
from ichor.ichor_lib.common.io import get_files_of_type, mkdir
from ichor.ichor_lib.common.os import input_with_prefill
from ichor.ichor_hpc import FILE_STRUCTURE
from ichor.ichor_lib.files import GJF, XYZ, Trajectory
from ichor.ichor_hpc import GLOBALS
from ichor.ichor_cli.menus.menu import Menu
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TycheCommand)

_input_file = None
_input_filetypes = [XYZ.filetype, GJF.filetype]

_n_molecules = 1

_solver = "periodic"

_box_size = 25.0


def write_freq_param(freq_param: Path, atoms: Atoms):
    atoms.centre()
    with open(freq_param, "w") as f:
        f.write(f"{'Sampling':<24}: Vibrate\n")
        f.write(f"{'Name':<24}: {GLOBALS.SYSTEM_NAME}\n")
        f.write(f"{'Temperature':<24}: {GLOBALS.TYCHE_TEMPERATURE}\n")
        f.write(f"{'NSeed':<24}: 1\n")
        f.write(f"{'NSample':<24}: {GLOBALS.TYCHE_STEPS}\n")
        f.write(f"{'Natoms':<24}: {len(atoms)}\n")
        f.write(f"{'Nsteps':<24}: 1000\n")
        f.write(f"{'Interactions':<24}: 1-4\n")
        f.write(f"{'WhichModes':<24}: All\n")
        f.write(f"{'MaxModes':<24}: {len(atoms.features[0])}\n")
        f.write(f"{'MCTemp':<24}: 300\n")


def submit_tyche(input_file: Path) -> JobID:
    if input_file.suffix == XYZ.filetype:
        atoms = XYZ(input_file).atoms
    elif input_file.suffix == GJF.filetype:
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    mkdir(FILE_STRUCTURE["tyche"])
    mkdir(FILE_STRUCTURE["tyche_g09"])
    g09_input = (
        FILE_STRUCTURE["tyche_g09"]
        / f"{GLOBALS.SYSTEM_NAME}{str(1).zfill(3)}.gjf"
    )
    g09_input = GJF(g09_input)
    g09_input.atoms = atoms
    g09_input.keywords += ["punch=derivatives"]
    g09_input.write()

    freq_param = FILE_STRUCTURE["tyche"] / "freq.param"
    write_freq_param(freq_param, atoms)

    with SubmissionScript(SCRIPT_NAMES["tyche"]) as submission_script:
        submission_script.add_command(TycheCommand(freq_param, g09_input.path))
        submission_script.add_command(
            ICHORCommand(
                func="tyche_to_xyz", func_args=[FILE_STRUCTURE["tyche"]]
            )
        )
        submission_script.add_command(
            ICHORCommand(
                func="set_points_location",
                func_args=[
                    f"{GLOBALS.SYSTEM_NAME}-tyche-{GLOBALS.TYCHE_TEMPERATURE}{Trajectory.filetype}"
                ],
            )
        )
    return submission_script.submit()


def tyche_to_xyz(tyche_input: Path, xyz: Optional[Path] = None) -> Path:
    xyzs = get_files_of_type(Trajectory.filetype, tyche_input.parent)
    if len(xyzs) == 0:
        raise FileNotFoundError(
            f"No trajectory files found in {tyche_input.parent}"
        )
    traj = Trajectory(xyzs[0])
    if xyz is None:
        xyz = Path(
            f"{GLOBALS.SYSTEM_NAME}-tyche-{GLOBALS.TYCHE_TEMPERATURE}{Trajectory.filetype}"
        )
    traj.write(xyz)
    return xyz


def set_temperature():
    while True:
        try:
            GLOBALS.TYCHE_TEMPERATURE = float(
                input_with_prefill(
                    "Enter Temperature (K): ",
                    prefill=f"{GLOBALS.TYCHE_TEMPERATURE}",
                )
            )
            break
        except ValueError:
            print("Temperature must be a number")


def set_nsteps():
    while True:
        try:
            GLOBALS.TYCHE_STEPS = int(
                input_with_prefill(
                    "Enter Temperature (K): ", prefill=f"{GLOBALS.TYCHE_STEPS}"
                )
            )
            break
        except ValueError:
            print("Temperature must be an integer")


def set_input():
    global _input_file
    _input_file = get_input_menu(_input_file, _input_filetypes)


def tyche_menu_refresh(menu):
    menu.clear_options()
    menu.add_option(
        "1", "Run TYCHE", submit_tyche, kwargs={"input_file": _input_file}
    )
    menu.add_space()
    menu.add_option("i", "Set input file", set_input)
    menu.add_option("t", "Set Temperature", set_temperature)
    menu.add_option("n", "Set number of timesteps", set_nsteps)
    menu.add_space()
    menu.add_message(f"Input File: {_input_file}")
    menu.add_message(f"Temperature: {GLOBALS.TYCHE_TEMPERATURE} K")
    menu.add_message(f"Number of Timesteps: {GLOBALS.TYCHE_STEPS:,}")
    menu.add_final_options()


def tyche_menu():
    global _input_file
    _input_file = get_first_file(Path(), _input_filetypes)
    with Menu("TYCHE Menu", refresh=tyche_menu_refresh):
        pass
