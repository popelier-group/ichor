from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions.user_input import (
    user_input_bool,
    user_input_int,
    user_input_path,
)
from ichor.core.files import Trajectory

TRAJ_SPLIT_MENU_DESCRIPTION = MenuDescription(
    "Trajectory Menu",
    subtitle="Use this to split a trajectory into point directories with single geometries.\n",
)


@dataclass
class TrajSplitMenuOptions(MenuOptions):
    selected_trajectory_path: Path = (
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
    )

    def check_selected_trajectory_path(self) -> Union[str, None]:
        """Checks whether the given Trjectory exists or if it is a file."""
        traj_path = Path(self.selected_trajectory_path)
        if not traj_path.exists():
            return f"Current trajectory path: {traj_path} does not exist."
        elif not traj_path.is_file():
            return f"Current trajectory path: {traj_path} is not a file."


# initialize dataclass for storing information for menu
traj_split_menu_options = TrajSplitMenuOptions()


# class with static methods for each menu item that calls a function.
class TrajSplitFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_trajectory():
        """function that asks user to update trajectory path."""
        traj_path = user_input_path("Enter Trajectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH = Path(
            traj_path
        ).absolute()
        traj_split_menu_options.selected_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
        )

    @staticmethod
    def split_trajectory_into_points_directory():
        """functions that splits a trajectory into a PointsDirectory."""
        default_to_center = True
        default_every = 1

        to_center = user_input_bool(
            f"Subtract centroid of geometries, default {default_to_center}: "
        )
        if to_center is None:
            to_center = default_to_center

        every = user_input_int(
            f"Write out every ith geometry, default {default_every}: "
        )
        if every is None:
            every = default_every

        traj = Trajectory(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)
        system_name = ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH.stem

        traj.to_dir(system_name, every, to_center)

    @staticmethod
    def split_trajectory_into_many_points_directories():
        """function that splits a given trajectory into many PointsDirectory-like directories."""
        default_split_size = 5000
        default_to_center = True
        default_every = 1

        nsplit = user_input_int(
            f"Enter split size integer (default {default_split_size}): "
        )
        if nsplit is None:
            nsplit = default_split_size

        to_center = user_input_bool(
            f"Subtract Centroid of Geometries (default {default_to_center}): "
        )
        if to_center is None:
            to_center = default_to_center

        every = user_input_int(
            f"Write out every ith geometry (give i) (default {default_every}): "
        )
        if every is None:
            every = default_every

        traj = Trajectory(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)

        system_name = ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH.stem

        traj.to_dirs(system_name, nsplit, every, to_center)


# initialize menu
traj_split_menu = ConsoleMenu(
    this_menu_options=traj_split_menu_options,
    title=TRAJ_SPLIT_MENU_DESCRIPTION.title,
    subtitle=TRAJ_SPLIT_MENU_DESCRIPTION.subtitle,
    prologue_text=TRAJ_SPLIT_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=TRAJ_SPLIT_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=TRAJ_SPLIT_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
traj_split_menu_items = [
    FunctionItem(
        "Select path of trajectory (.xyz)", TrajSplitFunctions.select_trajectory
    ),
    FunctionItem(
        "Split trajectory into single PointsDirectory-like dir",
        TrajSplitFunctions.split_trajectory_into_points_directory,
    ),
    FunctionItem(
        "Split trajectory into many PointsDirectories-like dirs",
        TrajSplitFunctions.split_trajectory_into_many_points_directories,
    ),
]

add_items_to_menu(traj_split_menu, traj_split_menu_items)
