# from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
# from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
# from consolemenu.format import MenuBorderStyleType
from ichor.cli.submenu_item import ConsoleMenu
# from consolemenu.items import CommandItem
# from ichor.core.files import PointsDirectory, Trajectory
from pathlib import Path
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from dataclasses import dataclass
# from typing import Union

POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION = MenuDescription("PointsDirectoryToDatabaseMenu", 
                                                        subtitle="Use this to convert PointsDirectory folder to a database.\n")

# initialize menu
points_directory_to_database_menu = ConsoleMenu(
                                    title=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.title,
                                    subtitle=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.subtitle,
                                    prologue_text = POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.prologue_description_text,
                                    epilogue_text=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.show_exit_option)

# # make menu items
# select_points_directory = FunctionItem("Select path of PointsDirectory", PointsDirectoryFunctions.select_points_directory)
# # TODO make a submenu for this to be able to select options to pass to PointsDirectory.from_trajectory
# convert_trajectory_to_points_directory = FunctionItem("Make PointsDirectory from .xyz trajectory", PointsDirectoryFunctions.convert_trajectory_to_points_directory)
# # TODO: make a submenu for this to be able to select options for the write_to_sqlite3_database function
# convert_points_directory_to_sqlite3_db = FunctionItem("Convert Current PointsDirectory into sqlite3 database.", PointsDirectoryFunctions.convert_points_directory_to_sqlite3_db)

# add items to menu
# points_directory_to_database_menu.append_item(select_points_directory)
# points_directory_to_database_menu.append_item(convert_trajectory_to_points_directory)
# points_directory_to_database_menu.append_item(convert_points_directory_to_sqlite3_db)