from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.core.files import PointsDirectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_descriptions import MenuDescription, MenuPrologue, update_menu_prologue
from dataclasses import dataclass, asdict

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", "Use this to do interact with ichor's PointsDirectory class.")

# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuPrologue(MenuPrologue):
    selected_points_directory: str = ""

# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:

    @staticmethod
    def select_points_directory():
        """ Asks user to update pointsdirectory and then updates PointsDirectoryMenuPrologue instance."""
        pd_path = user_input_path("Enter PointsDirectory Path: ")
        points_directory_menu_prologue.selected_points_directory = Path(pd_path).absolute()

    @staticmethod
    def convert_trajectory_to_points_directory():
        """ Converts given trajectory (.xyz) to a PointsDirectory-like structure."""
        trajectory_path = user_input_path("Enter Trajectory Path: ")
        pd = PointsDirectory.from_trajectory(trajectory_path)
        points_directory_menu_prologue.selected_points_directory = pd.path.absolute()

# initialize dataclass for storing information for menu
points_directory_menu_prologue = PointsDirectoryMenuPrologue()
# initialize menu
points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title, lambda: update_menu_prologue(points_directory_menu_prologue))

# make menu items
point_directory_path = FunctionItem("Select path of PointsDirectory", PointsDirectoryFunctions.select_points_directory)
trajectory_from_points_directory = FunctionItem("Make PointsDirectory from .xyz trajectory", PointsDirectoryFunctions.convert_trajectory_to_points_directory)

# add items to menu
points_directory_menu.append_item(point_directory_path)
points_directory_menu.append_item(trajectory_from_points_directory)


