from pathlib import Path

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.common.formatting import (
    format_number_with_comma,
    temperature_formatter,
)
from ichor.core.files import GJF, XYZ
from ichor.core.menu import Menu, MenuVar, set_number
from ichor.hpc import GLOBALS
from ichor.hpc.molecular_dynamics.cp2k import submit_cp2k

INPUT_FILETYPES = [XYZ.filetype, GJF.filetype]


def set_input(input_file: MenuVar[Path]):
    input_file.var = get_input_menu(input_file.var, INPUT_FILETYPES)


def cp2k_menu():
    input_file = MenuVar("Input File", get_first_file(Path(), INPUT_FILETYPES))
    temperature = MenuVar(
        "Temperature",
        GLOBALS.CP2K_TEMPERATURE,
        custom_formatter=temperature_formatter,
    )
    nsteps = MenuVar(
        "Number of Timesteps",
        GLOBALS.CP2K_STEPS,
        custom_formatter=format_number_with_comma,
    )

    with Menu("CP2K Menu") as menu:
        menu.add_option(
            "1",
            "Run CP2K",
            submit_cp2k,
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
