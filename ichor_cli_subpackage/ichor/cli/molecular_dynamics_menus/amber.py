from pathlib import Path

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.common.formatting import (
    format_number_with_comma,
    temperature_formatter,
)
from ichor.core.analysis.get_atoms import INPUT_FILETYPES
from ichor.core.menu import Menu, MenuVar, set_number
from ichor.hpc import GLOBALS
from ichor.hpc.molecular_dynamics.amber import submit_amber


def set_input(input_file: MenuVar[Path]):
    input_file.var = get_input_menu(input_file.var, INPUT_FILETYPES)


def timestep_formatter(write_every: int) -> str:
    return f"'{write_every}' timestep(s)"


def amber_menu():
    input_file = MenuVar("Input File", get_first_file(Path(), INPUT_FILETYPES))
    temperature = MenuVar(
        "Temperature",
        GLOBALS.AMBER_TEMPERATURE,
        custom_formatter=temperature_formatter,
    )
    nsteps = MenuVar(
        "Number of Timesteps",
        GLOBALS.AMBER_STEPS,
        custom_formatter=format_number_with_comma,
    )
    write_coord_every = MenuVar(
        "Write Output Every",
        GLOBALS.AMBER_STEPS,
        custom_formatter=timestep_formatter,
    )
    with Menu("Amber Menu") as menu:
        menu.add_option(
            "1", "Run Amber", submit_amber, args=[input_file, temperature]
        )
        menu.add_space()
        menu.add_option("i", "Set input file", set_input, args=[input_file])
        menu.add_option("t", "Set Temperature", set_number, args=[temperature])
        menu.add_option(
            "n", "Set number of timesteps", set_number, args=[nsteps]
        )
        menu.add_option(
            "e",
            "Set print every n timesteps",
            set_number,
            args=[write_coord_every],
        )
        menu.add_space()
        menu.add_var(input_file)
        menu.add_var(temperature)
        menu.add_var(nsteps)
        menu.add_var(write_coord_every)
