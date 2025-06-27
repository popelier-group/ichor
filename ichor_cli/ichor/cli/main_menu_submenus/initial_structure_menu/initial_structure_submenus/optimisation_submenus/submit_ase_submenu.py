from dataclasses import dataclass
from pathlib import Path
import traceback

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_free_flow,
    user_input_int,
    user_input_path,
)
from ichor.hpc.main.ase import submit_single_ase_xyz


SUBMIT_ASE_MENU_DESCRIPTION = MenuDescription(
    "Submit ASE Menu",
    subtitle="Use this menu to optimise a single geometry with ASE.\n",
)

SUBMIT_ASE_MENU_DEFAULTS = {
    "default_keywords": ["opt"],
    "default_method": "b3lyp",
    "default_basis_set": "6-31+g(d,p)",
    "default_ncores": 2,
    "default_gjf": "",
}


# dataclass used to store values for SubmitGaussianMenu
@dataclass
class SubmitGaussianMenuOptions(MenuOptions):
    selected_keywords: str
    selected_method: str
    selected_basis_set: str
    selected_number_of_cores: int
    selected_gjf_path: str


# initialize dataclass for storing information for menu
submit_ase_menu_options = SubmitGaussianMenuOptions(*SUBMIT_ASE_MENU_DEFAULTS.values())

# set keywords to opt as default
submit_ase_menu_options.selected_keywords = ["opt"]


# class with static methods for each menu item that calls a function.
class SubmitGaussianFunctions:
    @staticmethod
    def select_method():
        """Asks user to update the method for Gaussian"""
        submit_ase_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_ase_menu_options.selected_method
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation method selected {submit_ase_menu_options.selected_method}"
        )

    @staticmethod
    def select_basis_set():
        """Asks user to update the basis set."""
        submit_ase_menu_options.selected_basis_set = user_input_free_flow(
            "Enter basis set: ", submit_ase_menu_options.selected_basis_set
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation basis set selected {submit_ase_menu_options.selected_basis_set}"
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to update the basis set."""
        submit_ase_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_ase_menu_options.selected_number_of_cores,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Optimisation number of cores selected {submit_ase_menu_options.selected_number_of_cores}"
        )

    @staticmethod
    def xyz_to_ase_on_compute():
        """Creates and submits an optimisation using ase calculator."""
        (
            keywords,
            method,
            basis_set,
            ncores,
        ) = (
            submit_ase_menu_options.selected_keywords,
            submit_ase_menu_options.selected_method,
            submit_ase_menu_options.selected_basis_set,
            submit_ase_menu_options.selected_number_of_cores,
        )

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        submit_single_ase_xyz(
            input_xyz_path=xyz_path,
            ncores=ncores,
            keywords=keywords,
            method=method,
            basis_set=basis_set,
        )

        SUBMIT_ASE_MENU_DESCRIPTION.prologue_description_text = (
            "XYZ optimisation submitted successfully to ase \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"ase ptimisation job submitted for {xyz_path}"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_ase_menu_items = [
    FunctionItem(
        "Change method",
        SubmitGaussianFunctions.select_method,
    ),
    FunctionItem(
        "Change basis set",
        SubmitGaussianFunctions.select_basis_set,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitGaussianFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Submit to ase",
        SubmitGaussianFunctions.xyz_to_ase_on_compute,
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
