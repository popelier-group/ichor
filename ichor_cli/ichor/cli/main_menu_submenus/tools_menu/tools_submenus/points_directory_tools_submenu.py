from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path
from ichor.core.files import PointsDirectory, PointsDirectoryParent
from ichor.hpc.main import submit_check_points_directory_for_missing_files

POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION = MenuDescription(
    "PointsDirectory Menu",
    subtitle="Select a PointsDirectory and check it for missing files.",
)


# dataclass used to store values for PointsDirectoryToolsMenuOptions
@dataclass
class PointsDirectoryToolsMenuOptions(MenuOptions):
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
points_directory_tools_menu_options = PointsDirectoryToolsMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
)


# class with static methods for each menu item that calls a function.
class PointsDirectoryToolsMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates the menu options instance."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        points_directory_tools_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def submit_check_gaussian_and_aimall():
        """Submits job that checks Gaussian and AIMAll files for a given PointDirectory
        or PointsDirectoryParent instance."""

        pd_path = ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        submit_check_points_directory_for_missing_files(pd_path)


# initialize menu
points_directory_tools_menu = ConsoleMenu(
    this_menu_options=points_directory_tools_menu_options,
    title=POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.title,
    subtitle=POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.subtitle,
    prologue_text=POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=POINTS_DIRECTORY_TOOLS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
points_directory_tools_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        PointsDirectoryToolsMenuFunctions.select_points_directory,
    ),
    FunctionItem(
        "Submit check PointDirectory to compute.",
        PointsDirectoryToolsMenuFunctions.submit_check_gaussian_and_aimall,
    ),
]

add_items_to_menu(points_directory_tools_menu, points_directory_tools_menu_items)
