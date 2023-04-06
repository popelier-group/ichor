from ichor.cli.console_menu import ConsoleMenu
from consolemenu.items import SubmenuItem
from consolemenu.items import FunctionItem
from ichor.core.files import Trajectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from dataclasses import dataclass
from typing import Union
from ichor.cli.console_menu import add_items_to_menu
import ichor.cli.global_menu_variables

TRAJECTORY_MENU_DESCRIPTION = MenuDescription("Trajectory Menu", 
                                                        subtitle="Use this to interact with ichor's Trajectory class.\n")

@dataclass
class TrajectoryMenuOptions(MenuOptions):
    selected_trajectory_path: Path = ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH

    def check_selected_trajectory_path(self) -> Union[str, None]:
        """ Checks whether the given Trjectory exists or if it is a file."""
        traj_path = Path(self.selected_trajectory_path)
        if (not traj_path.exists()) or (not traj_path.is_file()):
            return f"Current {traj_path} does not exist or is not a file."

# initialize dataclass for storing information for menu
trajectory_menu_options = TrajectoryMenuOptions()

# class with static methods for each menu item that calls a function.
class TrajectoryFunctions:
    """ Functions that run when menu items are selected"""

    @staticmethod
    def select_trajectory():
        """ function that asks user to update trajectory path."""
        traj_path = user_input_path("Enter Trajectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH = Path(traj_path).absolute()
        trajectory_menu_options.selected_trajectory_path = ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH

# initialize menu
trajectory_menu = ConsoleMenu(this_menu_options=trajectory_menu_options,
                                    title=TRAJECTORY_MENU_DESCRIPTION.title,
                                    subtitle=TRAJECTORY_MENU_DESCRIPTION.subtitle,
                                    prologue_text = TRAJECTORY_MENU_DESCRIPTION.prologue_description_text,
                                    epilogue_text=TRAJECTORY_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=TRAJECTORY_MENU_DESCRIPTION.show_exit_option)

# make menu items
# can use lamda functions to change text of options as well :)
trajectory_menu_items = [FunctionItem("Select path of Trajectory", TrajectoryFunctions.select_trajectory),
                            ]

add_items_to_menu(trajectory_menu, trajectory_menu_items)