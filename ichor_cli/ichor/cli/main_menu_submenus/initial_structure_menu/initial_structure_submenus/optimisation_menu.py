from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.initial_structure_menu.initial_structure_submenus.optimisation_submenus import (
    submit_gaussian_menu,
    SUBMIT_GAUSSIAN_MENU_DESCRIPTION,
    submit_ase_menu,
    SUBMIT_ASE_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path

OPTIMISATION_MENU_DESCRIPTION = MenuDescription(
    "Optimisation Menu",
    subtitle="Use this menu to optimise an xyz file before generating trajectories for sampling.\n",
)


# dataclass used to store values for OptimisationMenu
@dataclass
class OptimisationMenuOptions(MenuOptions):
    selected_xyz_path: Path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH

    def check_selected_xyz_path(self) -> Union[str, None]:
        """Checks whether the given Trjectory exists or if it is a file."""

        xyz_path = Path(self.selected_xyz_path)
        if not xyz_path.exists():
            return f"Current path: {xyz_path} does not exist."
        elif not xyz_path.is_file():
            return f"Current path: {xyz_path} is not a file."
        elif not xyz_path.suffix == ".xyz":
            return f"Current path: {xyz_path} might not be a .xyz file."


# initialize dataclass for storing information for menu
optimisation_menu_options = OptimisationMenuOptions()


# class with static methods for each menu item that calls a function.
class OptimisationFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_xyz():
        """Asks user to update the .xyz file and then updates the MolecularDynamicsMenuOptions instance."""
        xyz_path = user_input_path("Enter .xyz Path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        optimisation_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )
        # update log file
        ichor.hpc.global_variables.LOGGER.info(
            f"XYZ file selected {optimisation_menu_options.selected_xyz_path}"
        )


# initialize menu
optimisation_menu = ConsoleMenu(
    this_menu_options=optimisation_menu_options,
    title=OPTIMISATION_MENU_DESCRIPTION.title,
    subtitle=OPTIMISATION_MENU_DESCRIPTION.subtitle,
    prologue_text=OPTIMISATION_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=OPTIMISATION_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=OPTIMISATION_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
optimisation_menu_items = [
    FunctionItem(
        "Select xyz file containing a single unoptimised geometry",
        OptimisationFunctions.select_xyz,
    ),
    SubmenuItem(
        SUBMIT_GAUSSIAN_MENU_DESCRIPTION.title,
        submit_gaussian_menu,
        optimisation_menu,

    ),
    SubmenuItem(
        SUBMIT_ASE_MENU_DESCRIPTION.title,
        submit_ase_menu, 
        optimisation_menu
    ),
]

add_items_to_menu(optimisation_menu, optimisation_menu_items)
