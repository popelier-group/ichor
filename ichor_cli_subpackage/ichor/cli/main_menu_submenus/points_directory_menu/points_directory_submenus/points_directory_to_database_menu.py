from ichor.cli.console_menu import ConsoleMenu
from ichor.core.files import PointsDirectory
from ichor.cli.menu_description import MenuDescription

POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION = MenuDescription("PointsDirectoryToDatabaseMenu", 
                                                        subtitle="Use this to convert PointsDirectory folder to a database.\n")

# initialize menu
points_directory_to_database_menu = ConsoleMenu(
                                    title=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.title,
                                    subtitle=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.subtitle,
                                    prologue_text = POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.prologue_description_text,
                                    epilogue_text=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.epilogue_description_text,
                                    show_exit_option=POINTS_DIRECTORY_TO_DATABASE_MENU_DESCRIPTION.show_exit_option)