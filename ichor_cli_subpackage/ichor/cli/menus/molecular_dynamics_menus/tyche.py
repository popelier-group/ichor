from pathlib import Path
from typing import Optional

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.atoms import Atoms
from ichor.core.common.formatting import (
    format_number_with_comma,
    temperature_formatter,
)
from ichor.core.common.io import get_files_of_type, mkdir
from ichor.core.files import GJF, XYZ, Trajectory
from ichor.core.menu import Menu, MenuVar, set_number
from ichor.hpc import FILE_STRUCTURE, GLOBALS
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    ICHORCommand,
    SubmissionScript,
    TycheCommand,
)

INPUT_FILETYPES = [XYZ.filetype, GJF.filetype]

# todo: move this to hpc/core


def write_freq_param(
    freq_param: Path, atoms: Atoms, temperature: float, nsteps: int
):
    atoms.centre()
    with open(freq_param, "w") as f:
        f.write(f"{'Sampling':<24}: Vibrate\n")
        f.write(f"{'Name':<24}: {GLOBALS.SYSTEM_NAME}\n")
        f.write(f"{'Temperature':<24}: {temperature}\n")
        f.write(f"{'NSeed':<24}: 1\n")
        f.write(f"{'NSample':<24}: {nsteps}\n")
        f.write(f"{'Natoms':<24}: {len(atoms)}\n")
        f.write(f"{'Nsteps':<24}: 1000\n")
        f.write(f"{'Interactions':<24}: 1-4\n")
        f.write(f"{'WhichModes':<24}: All\n")
        f.write(f"{'MaxModes':<24}: {len(atoms.features[0])}\n")
        f.write(f"{'MCTemp':<24}: 300\n")


def submit_tyche(input_file: Path, temperature: float, nsteps: int) -> JobID:
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
    write_freq_param(freq_param, atoms, temperature, nsteps)

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
                    f"{GLOBALS.SYSTEM_NAME}-tyche-{temperature}{Trajectory.filetype}"
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


def set_input(input_file: MenuVar[Path]):
    input_file.var = get_input_menu(input_file.var, INPUT_FILETYPES)


def tyche_menu():
    input_file = MenuVar("Input File", get_first_file(Path(), INPUT_FILETYPES))
    temperature = MenuVar(
        "Temperature",
        GLOBALS.TYCHE_TEMPERATURE,
        custom_formatter=temperature_formatter,
    )
    nsteps = MenuVar(
        "Number of Timesteps",
        GLOBALS.TYCHE_STEPS,
        custom_formatter=format_number_with_comma,
    )
    with Menu("TYCHE Menu") as menu:
        menu.add_option(
            "1",
            "Run TYCHE",
            submit_tyche,
            args=[input_file, temperature, nsteps],
        )
        menu.add_space()
        menu.add_option("i", "Set input file", set_input, args=[input_file])
        menu.add_option("t", "Set Temperature", set_number, args=[temperature])
        menu.add_option(
            "n", "Set number of timesteps", set_number, args=[nsteps]
        )
        menu.add_space()
        menu.add_var(input_file)
        menu.add_var(temperature)
        menu.add_var(nsteps)
