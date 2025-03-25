from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.initial_structure_menu.initial_structure_submenus import (
    file_conversion_menu,
    FILE_CONVERSION_MENU_DESCRIPTION,
    optimisation_menu,
    OPTIMISATION_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path

INITIAL_STRUCTURE_MENU_DESCRIPTION = MenuDescription(
    "Initial Structure Menu",
    subtitle="Hello hello hello.\n",
)


@dataclass
class InitialStructureMenuOptions(MenuOptions):

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
initial_structure_menu_options = InitialStructureMenuOptions()


class InitialStructureMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_xyz():
        """Asks user to update the .xyz file and then updates the MolecularDynamicsMenuOptions instance."""
        xyz_path = user_input_path("Enter .xyz Path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        initial_structure_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )


# initialize menu
initial_structure_menu = ConsoleMenu(
    this_menu_options=initial_structure_menu_options,
    title=INITIAL_STRUCTURE_MENU_DESCRIPTION.title,
    subtitle=INITIAL_STRUCTURE_MENU_DESCRIPTION.subtitle,
    prologue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=INITIAL_STRUCTURE_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
initial_structure_menu_items = [
    SubmenuItem(
        FILE_CONVERSION_MENU_DESCRIPTION.title,
        file_conversion_menu,
        initial_structure_menu,
    ),
    SubmenuItem(
        OPTIMISATION_MENU_DESCRIPTION.title, optimisation_menu, initial_structure_menu
    ),
    FunctionItem(
        "Set path to geometry for checking.",
        InitialStructureMenuFunctions.select_xyz,
    ),
]

add_items_to_menu(initial_structure_menu, initial_structure_menu_items)
