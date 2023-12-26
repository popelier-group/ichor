from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.molecular_dynamics_menu.molecular_dynamics_submenus import (
    amber_menu,
    AMBER_MENU_DESCRIPTION,
    cp2k_menu,
    CP2K_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path

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
                f"Current path: {xyz_path} does not exist or might not be a .xyz file\n"
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
        "Select xyz file containing MD starting geometry",
        MolecularDynamicsMenuFunctions.select_xyz,
    ),
    SubmenuItem(AMBER_MENU_DESCRIPTION.title, amber_menu, molecular_dynamics_menu),
    SubmenuItem(CP2K_MENU_DESCRIPTION.title, cp2k_menu, molecular_dynamics_menu),
]

add_items_to_menu(molecular_dynamics_menu, molecular_dynamics_menu_items)
