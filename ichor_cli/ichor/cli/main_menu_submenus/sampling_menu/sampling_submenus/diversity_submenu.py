from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_bool,
    user_input_int,
)
from ichor.hpc.main.ase import submit_single_ase_xyz


SUBMIT_DIVERSITY_MENU_DESCRIPTION = MenuDescription(
    "Submit Diversity Sampling Menu",
    subtitle="Use this menu to perform diversity sampling on a trajectory.\n",
)

SUBMIT_DIVERSITY_MENU_DEFAULTS = {
    "default_ncores": 2,
    "default_weights": False,
    "default_sample_size": 10000,
}


# dataclass used to store values for SubmitAseMenu
@dataclass
class SubmitDiversityMenuOptions(MenuOptions):
    selected_ncores: int
    selected_weights: bool
    selected_sample_size: int


# initialize dataclass for storing information for menu
submit_diversity_menu_options = SubmitDiversityMenuOptions(*SUBMIT_DIVERSITY_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class SubmitDiversityFunctions:
    @staticmethod
    def select_number_of_cores():
        """Asks user to select the number of cores."""
        submit_diversity_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_diversity_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_weights():
        """Asks user to select weights for either all atoms or only heavy atoms"""
        submit_diversity_menu_options.selected_weights = user_input_bool(
            "Restrict to heavy atoms (yes/no): ", submit_diversity_menu_options.selected_weights
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity sampling restricted to heavy atoms"
            f" {submit_diversity_menu_options.selected_weights}"
        )

    @staticmethod
    def select_sample_size():
        """Asks user to select the size of the sampled pool."""
        submit_diversity_menu_options.selected_sample_size = user_input_int(
            "Sample pool size: ",
            submit_diversity_menu.selected_sample_size,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity sample pool size {submit_diversity_menu_options.selected_sample_size}"
        )

    @staticmethod
    def xyz_to_ase_on_compute():
        """Creates and submits an optimisation using ase calculator."""
        (
            ncores,
            weights,
            sample_size,
        ) = (
            submit_diversity_menu_options.selected_ncores,
            submit_diversity_menu_options.selected_weights,
            submit_diversity_menu_options.selected_sample_size,
        )

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)
        trajectory_path=Path(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)

        submit_single_ase_xyz(
            input_trajector=trajectory_path,
            input_xyz_path=xyz_path,
            ncores=ncores,
            weights=weights,
            sample_size=sample_size,
        )

        SUBMIT_DIVERSITY_MENU_DESCRIPTION.prologue_description_text = (
            "XYZ optimisation submitted successfully to ASE \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity sampling job submitted for {xyz_path}"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_diversity_menu_items = [
    FunctionItem(
        "Change method",
        SubmitDiversityFunctions.select_method,
    ),
    FunctionItem(
        "Change cores",
        SubmitDiversityFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change solvent",
        SubmitDiversityFunctions.select_solvent,
    ),

]

# initialize menu
submit_diversity_menu = ConsoleMenu(
    this_menu_options=submit_diversity_menu_options,
    title=SUBMIT_DIVERSITY_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_DIVERSITY_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_DIVERSITY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_DIVERSITY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_DIVERSITY_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_diversity_menu, submit_diversity_menu_items)
