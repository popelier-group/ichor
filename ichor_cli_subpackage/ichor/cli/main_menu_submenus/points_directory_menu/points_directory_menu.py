# from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
# from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
# from consolemenu.format import MenuBorderStyleType
from ichor.cli.console_menu import ConsoleMenu
from consolemenu.items import SubmenuItem
from consolemenu.items import FunctionItem
from ichor.core.files import PointsDirectory, Trajectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from dataclasses import dataclass
from typing import Union
from ichor.cli.main_menu_submenus.points_directory_menu.points_directory_submenus.points_directory_to_database_menu import points_directory_to_database_menu, \
    POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION
from ichor.cli.console_menu import add_items_to_menu
import ichor.cli.global_menu_variables

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", 
                                                        subtitle="Use this to interact with ichor's PointsDirectory class.\n")

# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_points_directory_path: Path = ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """ Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (not pd_path.exists()) or (not pd_path.is_dir()):
            return f"Current {pd_path} does not exist or is not a directory."

# initialize dataclass for storing information for menu
points_directory_menu_options = PointsDirectoryMenuOptions()

# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:
    """ Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """ Asks user to update points directory and then updates PointsDirectoryMenuPrologue instance."""
        pd_path = user_input_path("Enter PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(pd_path).absolute()
        points_directory_menu_options.selected_points_directory_path = ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH

    # TODO: move these to sub menus
    # @staticmethod
    # def convert_trajectory_to_points_directory():
    #     """ Converts given trajectory (.xyz) to a PointsDirectory-like structure."""
    #     trajectory_path = user_input_path("Enter Trajectory Path: ")
    #     pd = PointsDirectory.from_trajectory(trajectory_path)
    #     points_directory_menu_options.selected_points_directory_path = pd.path.absolute()

    # @staticmethod
    # def convert_points_directory_to_sqlite3_db():
    #     """ Converts selected PointsDirectory to Sqllite3 database."""
    #     pd_path = points_directory_menu_options.selected_points_directory_path
    #     PointsDirectory(pd_path).write_to_sqlite3_database()

# initialize menu
points_directory_menu = ConsoleMenu(this_menu_options=points_directory_menu_options,
                                    title=POINTS_DIRECTORY_MENU_DESCRIPTION.title,
                                    subtitle=POINTS_DIRECTORY_MENU_DESCRIPTION.subtitle,
                                    prologue_text = POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text,
                                    epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option)

# make menu items
# can use lamda functions to change text of options as well :)
point_directory_menu_items = [FunctionItem("Select path of PointsDirectory", PointsDirectoryFunctions.select_points_directory),
                              SubmenuItem(text=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.title, submenu=points_directory_to_database_menu,
                                menu=points_directory_menu)
]

add_items_to_menu(points_directory_menu, point_directory_menu_items)

# TODO make a submenu for this to be able to select options to pass to PointsDirectory.from_trajectory
# convert_trajectory_to_points_directory = FunctionItem("Make PointsDirectory from .xyz trajectory", PointsDirectoryFunctions.convert_trajectory_to_points_directory)
# # TODO: make a submenu for this to be able to select options for the write_to_sqlite3_database function
# convert_points_directory_to_sqlite3_db = FunctionItem("Convert Current PointsDirectory into sqlite3 database.", PointsDirectoryFunctions.convert_points_directory_to_sqlite3_db)

# add items to menu
# points_directory_menu.append_item(select_points_directory)
# points_directory_menu.append_item(submenu1)
# points_directory_menu.append_item(convert_trajectory_to_points_directory)
# points_directory_menu.append_item(convert_points_directory_to_sqlite3_db)