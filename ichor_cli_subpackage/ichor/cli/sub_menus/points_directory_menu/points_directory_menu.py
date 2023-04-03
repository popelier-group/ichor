from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.core.files import PointsDirectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_descriptions import MenuDescription, MenuPrologue, update_menu_prologue
from dataclasses import dataclass, asdict

# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuPrologue(MenuPrologue):
    selected_points_directory: str = ""

# initialize dataclass
points_directory_menu_prologue = PointsDirectoryMenuPrologue()

# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:

    @staticmethod
    def select_points_directory():
        """ Asks user to update pointsdirectory and then updates PointsDirectoryMenuPrologue instance."""
        val = user_input_path("Enter PointsDirectory Path: ")
        points_directory_menu_prologue.selected_points_directory = val

POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription("PointsDirectory Menu", "Use this to do interact with ichor's PointsDirectory class.")

points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title, lambda: update_menu_prologue(points_directory_menu_prologue))

# selection_menu = SelectionMenu([d for d in Path().iterdir() if d.is_dir()])
# selection_items = SubmenuItem("Select Directory", selection_menu, points_directory_menu)
# points_directory_menu.append_item(selection_items)

accept_user_input_path = FunctionItem("Write path for PointsDirectory", PointsDirectoryFunctions.select_points_directory)

points_directory_menu.append_item(accept_user_input_path)
# new_points_location = accept_user_input_path.get_return()
# points_directory_menu.prologue_text = new_points_location
# points_directory_menu.draw()
# make_points_dir_from_trajectory = FunctionItem("Make trajectory from PointsDirectory", PointsDirectory.from_trajectory, )


