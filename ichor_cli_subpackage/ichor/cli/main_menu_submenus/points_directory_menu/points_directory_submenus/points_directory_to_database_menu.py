from ichor.cli.console_menu import ConsoleMenu
from ichor.core.files import PointsDirectory
from ichor.cli.menu_description import MenuDescription
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu
import ichor.cli.global_menu_variables

POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION = MenuDescription("PointsDirectoryToDatabaseMenu", 
                                                        subtitle="Use this to convert PointsDirectory folder to a database.\n")




# class with static methods for each menu item that calls a function.
class PointsDirectoryToDatabaseFunctions:
    """ Functions that run when menu items are selected"""

    @staticmethod
    def convert_points_directory_to_sqlite3_db():
        """ Converts selected PointsDirectory to Sqlite3 database."""
        pd_path = ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        PointsDirectory(pd_path).write_to_sqlite3_database()

# initialize menu
points_directory_to_database_menu = ConsoleMenu(
                                    title=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.title,
                                    subtitle=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.subtitle,
                                    prologue_text = POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.prologue_description_text,
                                    epilogue_text=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.show_exit_option)

# can use lamda functions to change text of options as well :)
points_directory_to_database_items = [FunctionItem("Convert PointsDirectory to SQLite3 database.", 
                                            PointsDirectoryToDatabaseFunctions.convert_points_directory_to_sqlite3_db)]

add_items_to_menu(points_directory_to_database_menu, points_directory_to_database_items)