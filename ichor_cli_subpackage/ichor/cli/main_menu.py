# Import the necessary packages
from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.main_menu_submenus.points_directory_menu import points_directory_menu
from ichor.cli.main_menu_submenus.analysis_menu import analysis_menu
from ichor.cli.main_menu_submenus.molecular_dynamics_menu.molecular_dynamics_menu import molecular_dynamics_menu
from ichor.cli.main_menu_submenus.tools_menu.tools_menu import tools_menu
from ichor.cli.menu_description import MenuDescription

# import menu decriptions
from ichor.cli.main_menu_submenus import POINTS_DIRECTORY_MENU_DESCRIPTION, ANALYSIS_MENU_DESCRIPTION, \
        MOLECULAR_DYNAMICS_MENU_DESCRIPTION, TOOLS_MENU_DESCRIPTION

# points_directory_menu = ConsoleMenu(POINTS_DIRECTORY_MENU_DESCRIPTION.title,
#                                     subtitle=POINTS_DIRECTORY_MENU_DESCRIPTION.subtitle,
#                                     prologue_text = lambda: POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text + points_directory_menu_options(),
#                                     epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
#                                     show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option)


MAIN_MENU_DESCRIPTION = MenuDescription("Main Menu", subtitle="Welcome to ichor's main menu!", show_exit_option=True)

# create main menu
main_menu = ConsoleMenu(MAIN_MENU_DESCRIPTION.title,
                        subtitle=MAIN_MENU_DESCRIPTION.subtitle,
                        prologue_text=MAIN_MENU_DESCRIPTION.prologue_description_text,
                        epilogue_text=MAIN_MENU_DESCRIPTION.epilogue_description_text,
                        show_exit_option=MAIN_MENU_DESCRIPTION.show_exit_option
                        )

# make submenus
main_menu_submenus = [SubmenuItem(POINTS_DIRECTORY_MENU_DESCRIPTION.title, points_directory_menu, main_menu),
                      SubmenuItem(ANALYSIS_MENU_DESCRIPTION.title, analysis_menu, main_menu),
                      SubmenuItem(MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title, molecular_dynamics_menu, main_menu),
                      SubmenuItem(TOOLS_MENU_DESCRIPTION.title, tools_menu, main_menu)
                    ]

# add submenus to main menu
for submenu in main_menu_submenus:
    main_menu.append_item(submenu)

# this function will be used by setuptools entry points
def run_main_menu():
    """ Runs main ichor menu."""
    main_menu.show()
