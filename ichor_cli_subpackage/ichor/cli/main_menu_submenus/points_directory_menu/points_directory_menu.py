from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from consolemenu.format import MenuBorderStyleType
from ichor.core.files import PointsDirectory, Trajectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_descriptions import MenuDescription, MenuOptions
from dataclasses import dataclass
from typing import Union

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", 
                                                        prologue_description_text="Use this to do interact with ichor's PointsDirectory class.\n")

# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_points_directory_path: Path = Path("").absolute()

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """ Checks whether the given PointsDirectory exists or if it is a directory """
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
        points_directory_menu_options.selected_points_directory_path = Path(pd_path).absolute()

    @staticmethod
    def convert_trajectory_to_points_directory():
        """ Converts given trajectory (.xyz) to a PointsDirectory-like structure."""
        trajectory_path = user_input_path("Enter Trajectory Path: ")
        pd = PointsDirectory.from_trajectory(trajectory_path)
        points_directory_menu_options.selected_points_directory_path = pd.path.absolute()

    @staticmethod
    def convert_points_directory_to_sqlite3_db():
        """ Converts selected PointsDirectory to Sqllite3 database."""
        pd_path = points_directory_menu_options.selected_points_directory_path
        PointsDirectory(pd_path).write_to_sqlite3_database()

points_directory_menu_functions = PointsDirectoryFunctions()

# initialize menu
points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title,
                                    prologue_text = lambda: POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text + points_directory_menu_options(),
                                    epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option)

# make menu items
select_points_directory = FunctionItem("Select path of PointsDirectory", PointsDirectoryFunctions.select_points_directory)
# TODO make a submenu for this to be able to select options to pass to PointsDirectory.from_trajectory
convert_trajectory_to_points_directory = FunctionItem("Make PointsDirectory from .xyz trajectory", PointsDirectoryFunctions.convert_trajectory_to_points_directory)
# TODO: make a submenu for this to be able to select options for the write_to_sqlite3_database function
convert_points_directory_to_sqlite3_db = FunctionItem("Convert Current PointsDirectory into sqlite3 database.", PointsDirectoryFunctions.convert_points_directory_to_sqlite3_db)

# add items to menu
points_directory_menu.append_item(select_points_directory)
points_directory_menu.append_item(convert_trajectory_to_points_directory)
points_directory_menu.append_item(convert_points_directory_to_sqlite3_db)