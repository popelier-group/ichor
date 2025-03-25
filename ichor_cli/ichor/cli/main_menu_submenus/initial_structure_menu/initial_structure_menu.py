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
from ichor.core.files import PointsDirectory, PointsDirectoryParent

INITIAL_STRUCTURE_MENU_DESCRIPTION = MenuDescription(
    "Initial Structure Menu",
    subtitle="Hello hello hello.\n",
)


# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_points_directory_path: Path

    def check_path(self):

        pd_path = Path(self.selected_points_directory_path)
        if not pd_path.is_dir():
            return "Current path is not a directory."

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (pd_path.suffix != PointsDirectory._suffix) and (
            pd_path.suffix != PointsDirectoryParent._suffix
        ):
            return f"Current path: {pd_path} might not be PointsDirectory-like)."


# initialize dataclass for storing information for menu
points_directory_menu_options = PointsDirectoryMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
)


# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        points_directory_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )


# initialize menu
initial_structure_menu = ConsoleMenu(
    this_menu_options=points_directory_menu_options,
    title=INITIAL_STRUCTURE_MENU_DESCRIPTION.title,
    subtitle=INITIAL_STRUCTURE_MENU_DESCRIPTION.subtitle,
    prologue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=INITIAL_STRUCTURE_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
point_directory_menu_items = [
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
        PointsDirectoryFunctions.select_points_directory,
    ),
]

add_items_to_menu(initial_structure_menu, point_directory_menu_items)
