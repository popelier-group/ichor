from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.points_directory_menu.points_directory_submenus import (
    submit_aimall_menu,
    SUBMIT_AIMALL_MENU_DESCRIPTION,
    submit_database_menu,
    SUBMIT_DATABASE_MENU_DESCRIPTION,
    submit_gaussian_menu,
    SUBMIT_GAUSSIAN_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path, user_input_bool, user_input_int
from ichor.core.files import PointsDirectory, PointsDirectoryParent, Trajectory

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription(
    "PointsDirectory Menu",
    subtitle="Use this to create and interact with ichor's PointsDirectory class.\n",
)


# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_points_directory_path: Path

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
    def select_trajectory():
        """function that asks user to update trajectory path."""
        traj_path = user_input_path("Enter Trajectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH = Path(
            traj_path
        ).absolute()
        points_directory_menu_options.selected_trajectory_path = (
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
points_directory_menu = ConsoleMenu(
    this_menu_options=points_directory_menu_options,
    title=POINTS_DIRECTORY_MENU_DESCRIPTION.title,
    subtitle=POINTS_DIRECTORY_MENU_DESCRIPTION.subtitle,
    prologue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
point_directory_menu_items = [
    FunctionItem(
        "Select path of trajectory", PointsDirectoryFunctions.select_trajectory
    ),
    FunctionItem(
        "Split trajectory into single PointsDirectory-like dir",
        PointsDirectoryFunctions.split_trajectory_into_points_directory,
    ),
    FunctionItem(
        "Split trajectory into many PointsDirectories-like dirs",
        PointsDirectoryFunctions.split_trajectory_into_many_points_directories,
    ),
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        PointsDirectoryFunctions.select_points_directory,
    ),
    SubmenuItem(
        SUBMIT_GAUSSIAN_MENU_DESCRIPTION.title,
        submit_gaussian_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        SUBMIT_AIMALL_MENU_DESCRIPTION.title, submit_aimall_menu, points_directory_menu
    ),
    SubmenuItem(
        SUBMIT_DATABASE_MENU_DESCRIPTION.title,
        submit_database_menu,
        points_directory_menu,
    ),
]

add_items_to_menu(points_directory_menu, point_directory_menu_items)
