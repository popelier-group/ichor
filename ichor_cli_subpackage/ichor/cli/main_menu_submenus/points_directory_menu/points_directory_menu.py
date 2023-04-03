from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from consolemenu.format import MenuBorderStyleType
from ichor.core.files import PointsDirectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_descriptions import MenuDescription, MenuPrologue, update_menu_prologue_or_epilogue
from dataclasses import dataclass

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", "Use this to do interact with ichor's PointsDirectory class.")

# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuPrologue(MenuPrologue):
    selected_points_directory_path: Path = Path("").absolute()

# initialize dataclass for storing information for menu
points_directory_menu_prologue = PointsDirectoryMenuPrologue()

class PointsDirectoryMenuEpilogue:

    @staticmethod
    def check_selected_points_directory_path(pd_path):

        pd_path = Path(pd_path)
        if (not pd_path.exists()) or (not pd_path.is_dir()):
            return "Current points_directory_path is not a directory."
        else:
            return ""

    def __str__(self):
        return "Warnings\n" + PointsDirectoryMenuEpilogue.check_selected_points_directory_path(points_directory_menu_prologue.selected_points_directory_path)

points_directory_menu_epilogue = PointsDirectoryMenuEpilogue()

# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:

    @staticmethod
    def select_points_directory():
        """ Asks user to update pointsdirectory and then updates PointsDirectoryMenuPrologue instance."""
        pd_path = user_input_path("Enter PointsDirectory Path: ")
        points_directory_menu_prologue.selected_points_directory_path = Path(pd_path).absolute()

    @staticmethod
    def convert_trajectory_to_points_directory():
        """ Converts given trajectory (.xyz) to a PointsDirectory-like structure."""
        trajectory_path = user_input_path("Enter Trajectory Path: ")
        pd = PointsDirectory.from_trajectory(trajectory_path)
        points_directory_menu_prologue.selected_points_directory_path = pd.path.absolute()

    @staticmethod
    def convert_points_directory_to_sqlite3_db():
        pd_path = points_directory_menu_prologue.selected_points_directory_path
        PointsDirectory(pd_path).write_to_sqlite3_database()

# initialize menu
points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title,
                                    prologue_text = lambda: update_menu_prologue_or_epilogue(points_directory_menu_prologue),
                                    epilogue_text= lambda: update_menu_prologue_or_epilogue(points_directory_menu_epilogue))

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


