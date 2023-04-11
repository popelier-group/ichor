from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_free_flow,
    user_input_int,
    user_input_path,
)
from ichor.hpc.molecular_dynamics import submit_amber, submit_cp2k


def ask_user_for_cp2k_settings():

    default_method = "BLYP"
    default_basis_set = "6-31G*"
    default_temperature = 300
    default_nsteps = 10_000
    default_molecular_charge = 0
    default_spin_multiplicity = 1
    default_number_of_cores = 8

    method = user_input_free_flow(
        f"Method for CP2K calculations, default {default_method}: "
    )
    if method is None:
        method = default_method

    basis_set = user_input_free_flow(
        f"Basis set for CP2K calculations, default {default_basis_set}: "
    )
    if basis_set is None:
        basis_set = default_basis_set

    temperature = user_input_int(
        f"Temperature for CP2K simulation, default {default_temperature}: "
    )
    if temperature is None:
        temperature = default_temperature

    nsteps = user_input_int(
        f"Number of steps for CP2K simulation, default {default_nsteps}: "
    )
    if nsteps is None:
        nsteps = default_nsteps

    molecular_charge = user_input_int(
        f"Molecular charge of system, default {default_molecular_charge}: "
    )
    if molecular_charge is None:
        molecular_charge = default_molecular_charge

    spin_multiplicity = user_input_int(
        f"Spin multiplicity charge of system, default {default_spin_multiplicity}: "
    )
    if spin_multiplicity is None:
        spin_multiplicity = default_spin_multiplicity

    ncores = user_input_int(
        f"Number of cores for CP2K simulation, default {default_number_of_cores}: "
    )
    if ncores is None:
        ncores = default_number_of_cores

    return (
        method,
        basis_set,
        temperature,
        nsteps,
        molecular_charge,
        spin_multiplicity,
        ncores,
    )


def ask_user_for_amber_settings():

    default_temperature = 1000
    default_nsteps = 1_000_000
    default_write_coord_every = 10
    default_dt = 0.001
    default_ln_gamma = 0.7

    temperature = user_input_int(
        f"Temperature for AMBER simulation, default {default_temperature}: "
    )
    if temperature is None:
        temperature = default_temperature

    nsteps = user_input_int(
        f"Number of timesteps for AMBER simulation, default {default_nsteps}: "
    )
    if nsteps is None:
        nsteps = default_nsteps

    write_coord_every = user_input_int(
        f"Write coordinates every n-th step, default {default_write_coord_every}: "
    )
    if write_coord_every is None:
        write_coord_every = default_write_coord_every

    dt = user_input_int(f"Timestep time in picoseconds, default {default_dt}: ")
    if dt is None:
        dt = default_dt

    ln_gamma = user_input_int(
        f"Collision frequency in picoseconds, default {default_ln_gamma}: "
    )
    if ln_gamma is None:
        ln_gamma = default_ln_gamma

    return temperature, nsteps, write_coord_every, dt, ln_gamma


MOLECULAR_DYNAMICS_MENU_DESCRIPTION = MenuDescription(
    "Molecular Dynamics Menu", subtitle="Use this to submit MD simulations with ichor."
)


@dataclass
class MolecularDynamicsMenuOptions(MenuOptions):
    selected_xyz_path: Path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH

    def check_selected_xyz_path(self) -> Union[str, None]:
        """Checks whether the given Trjectory exists or if it is a file."""
        xyz_path = Path(self.selected_xyz_path)
        if (
            (not xyz_path.exists())
            or (not xyz_path.is_file())
            or (not xyz_path.suffix == ".xyz")
        ):
            return (
                f"Current path: {xyz_path} does not exist or might not be a .xyz file"
            )


# initialize dataclass for storing information for menu
molecular_dynamics_menu_options = MolecularDynamicsMenuOptions()


class MolecularDynamicsMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_xyz():
        """Asks user to update the .xyz file and then updates the MolecularDynamicsMenuOptions instance."""
        xyz_path = user_input_path("Enter .xyz Path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        molecular_dynamics_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )

    @staticmethod
    def submit_cp2k_to_compute():
        """Asks for user input and submits CP2K job to compute node."""

        (
            method,
            basis_set,
            temperature,
            nsteps,
            molecular_charge,
            spin_multiplicity,
            ncores,
        ) = ask_user_for_cp2k_settings()

        submit_cp2k(
            input_file=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            system_name=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH.stem,
            temperature=temperature,
            nsteps=nsteps,
            method=method,
            basis_set=basis_set,
            molecular_charge=molecular_charge,
            spin_multiplicity=spin_multiplicity,
            ncores=ncores,
        )

    @staticmethod
    def submit_amber_to_compute():
        """Asks for user input and submits AMBER job to compute node."""

        (
            temperature,
            nsteps,
            write_coord_every,
            dt,
            ln_gamma,
        ) = ask_user_for_amber_settings()

        submit_amber(
            input_file_path=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            temperature=temperature,
            nsteps=nsteps,
            write_coord_every=write_coord_every,
            system_name=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH.stem,
            dt=dt,
            ln_gamma=ln_gamma,
        )


# initialize menu
molecular_dynamics_menu = ConsoleMenu(
    this_menu_options=molecular_dynamics_menu_options,
    title=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title,
    subtitle=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.subtitle,
    prologue_text=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=MOLECULAR_DYNAMICS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
molecular_dynamics_menu_items = [
    FunctionItem(
        "Select path of .xyz file containing MD starting geometry",
        MolecularDynamicsMenuFunctions.select_xyz,
    ),
    FunctionItem(
        "Submit .xyz file to AMBER",
        MolecularDynamicsMenuFunctions.submit_amber_to_compute,
    ),
    FunctionItem(
        "Submit .xyz file to CP2K",
        MolecularDynamicsMenuFunctions.submit_cp2k_to_compute,
    ),
]

add_items_to_menu(molecular_dynamics_menu, molecular_dynamics_menu_items)
