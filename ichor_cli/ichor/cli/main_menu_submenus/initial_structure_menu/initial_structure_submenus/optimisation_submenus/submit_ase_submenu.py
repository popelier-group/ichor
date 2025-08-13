from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_bool,
)
from ichor.hpc.main.ase import submit_single_ase_xyz


SUBMIT_ASE_MENU_DESCRIPTION = MenuDescription(
    "Submit ASE Menu",
    subtitle="Use this menu to optimise a single geometry with ASE.\n",
)

SUBMIT_ASE_MENU_DEFAULTS = {
    "default_method": "GFN2-xTB",
    "default_ncores": 2,
    "default_solvent": "none",
    "default_electronic_temperature": 300,
    "default_max_iterations": 2048,
    "default_fmax": 0.01,
    "overwite_existing": False,
}


# dataclass used to store values for SubmitAseMenu
@dataclass
class SubmitAseMenuOptions(MenuOptions):
    selected_method: str
    selected_ncores: int
    selected_solvent: str
    selected_electronic_temperature: int
    selected_max_iterations: int
    selected_fmax: float
    selected_overwrite: bool


# initialize dataclass for storing information for menu
submit_ase_menu_options = SubmitAseMenuOptions(*SUBMIT_ASE_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class SubmitAseFunctions:
    @staticmethod
    # Probably need to make this restricted/do we even want this as an option?
    def select_method():
        """Asks user to update the method for ASE"""
        submit_ase_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_ase_menu_options.selected_method
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation method selected {submit_ase_menu_options.selected_method}"
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to update the basis set."""
        submit_ase_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_ase_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_solvent():
        """Asks user to update the solvent choice."""
        submit_ase_menu_options.selected_solvent = user_input_free_flow(
            "Enter solvent choice: ", submit_ase_menu_options.solvent
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation solvent selected {submit_ase_menu_options.solvent}"
        )

    @staticmethod
    def select_electronic_temperature():
        """Asks user to update the electronic temperature."""
        submit_ase_menu_options.selected_electronic_temperature = user_input_int(
            "Enter electronic temperature: ",
            submit_ase_menu_options.selected_electronic_temperature,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation electronic temperature selected {submit_ase_menu_options.selected_electronic_temperature}"
        )

    @staticmethod
    def select_max_iterations():
        """Asks user to update the number of max iterations."""
        submit_ase_menu_options.selected_max_iterations = user_input_int(
            "Enter max number of iterations: ",
            submit_ase_menu_options.selected_max_iterations,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Max number of iterations selected {submit_ase_menu_options.selected_max_iterations}"
        )

    @staticmethod
    def select_fmax():
        """Asks user to update the max force to stop at."""
        submit_ase_menu_options.selected_fmax = user_input_float(
            "Enter max force: ",
            submit_ase_menu_options.selected_fmax,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation max force selected {submit_ase_menu_options.selected_fmax}"
        )

    @staticmethod
    def select_overwrite_existing_calc():
        """Asks user whether or not to overwrite existing calculation"""
        submit_ase_menu_options.selected_overwrite = user_input_bool(
            "Overwrite existing calculation (yes/no): ",
            submit_ase_menu_options.selected_overwrite,
        )

    @staticmethod
    def xyz_to_ase_on_compute():
        """Creates and submits an optimisation using ase calculator."""
        (
            method,
            ncores,
            solvent,
            electronic_temperature,
            max_iterations,
            fmax,
            overwrite,
        ) = (
            submit_ase_menu_options.selected_method,
            submit_ase_menu_options.selected_ncores,
            submit_ase_menu_options.selected_solvent,
            submit_ase_menu_options.selected_electronic_temperature,
            submit_ase_menu_options.selected_max_iterations,
            submit_ase_menu_options.selected_fmax,
            submit_ase_menu_options.selected_overwrite,
        )

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        submit_single_ase_xyz(
            input_xyz_path=xyz_path,
            method=method,
            ncores=ncores,
            solvent=solvent,
            electronic_temperature=electronic_temperature,
            max_iterations=max_iterations,
            fmax=fmax,
            overwrite=overwrite,
        )

        SUBMIT_ASE_MENU_DESCRIPTION.prologue_description_text = (
            "XYZ optimisation submitted successfully to ASE \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"ASE optimisation job submitted for {xyz_path}"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_ase_menu_items = [
    FunctionItem(
        "Change method",
        SubmitAseFunctions.select_method,
    ),
    FunctionItem(
        "Change cores",
        SubmitAseFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change solvent",
        SubmitAseFunctions.select_solvent,
    ),
    FunctionItem(
        "Change electronic temperature",
        SubmitAseFunctions.select_electronic_temperature,
    ),
    FunctionItem(
        "Change max iterations",
        SubmitAseFunctions.select_max_iterations,
    ),
    FunctionItem(
        "Change max force",
        SubmitAseFunctions.select_fmax,
    ),
    FunctionItem(
        "Overwrite existing calculation",
        SubmitAseFunctions.select_overwrite_existing_calc,
    ),
    FunctionItem(
        "Submit to ASE",
        SubmitAseFunctions.xyz_to_ase_on_compute,
    ),
]

# initialize menu
submit_ase_menu = ConsoleMenu(
    this_menu_options=submit_ase_menu_options,
    title=SUBMIT_ASE_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_ASE_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_ASE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_ASE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_ASE_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_ase_menu, submit_ase_menu_items)
