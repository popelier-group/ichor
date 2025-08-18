from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.trajectory_creation_menu.trajectory_creation_submenus import (
    metadynamics_menu,
    METADYNAMICS_MENU_DESCRIPTION,
    amber_menu,
    AMBER_MENU_DESCRIPTION,
    cp2k_menu,
    CP2K_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path

TRAJECTORY_CREATION_MENU_DESCRIPTION = MenuDescription(
    "Trajectory Creation Menu",
    subtitle="Use this to submit molecular dynamics or metadynamics simulations with ichor to create geometry sample pool.",
)


@dataclass
class TrajectoryCreationMenuOptions(MenuOptions):

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
trajectory_creation_menu_options = TrajectoryCreationMenuOptions()


class TrajectoryCreationMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_xyz():
        """Asks user to update the .xyz file and then updates the TrajectoryCreationMenuOptions instance."""
        xyz_path = user_input_path("Enter .xyz Path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        trajectory_creation_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )


# initialize menu
trajectory_creation_menu = ConsoleMenu(
    this_menu_options=trajectory_creation_menu_options,
    title=TRAJECTORY_CREATION_MENU_DESCRIPTION.title,
    subtitle=TRAJECTORY_CREATION_MENU_DESCRIPTION.subtitle,
    prologue_text=TRAJECTORY_CREATION_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=TRAJECTORY_CREATION_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=TRAJECTORY_CREATION_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
trajectory_creation_menu_items = [
    FunctionItem(
        "Select xyz file containing Molecular Dynamics or Metadynamics starting geometry",
        TrajectoryCreationMenuFunctions.select_xyz,
    ),
    SubmenuItem(
        METADYNAMICS_MENU_DESCRIPTION.title, metadynamics_menu, trajectory_creation_menu
    ),
    SubmenuItem(AMBER_MENU_DESCRIPTION.title, amber_menu, trajectory_creation_menu),
    SubmenuItem(CP2K_MENU_DESCRIPTION.title, cp2k_menu, trajectory_creation_menu),
]

add_items_to_menu(trajectory_creation_menu, trajectory_creation_menu_items)
