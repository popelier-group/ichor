# Import the necessary packages
from consolemenu import ConsoleMenu, SelectionMenu, MultiSelectMenu, MenuFormatBuilder, PromptUtils, Screen, items, clear_terminal
from consolemenu.items import CommandItem, ExitItem, ExternalItem, FunctionItem, MenuItem, SelectionItem, SubmenuItem
from ichor.cli.sub_menus.points_directory_menu import points_directory_menu
from ichor.cli.sub_menus.analysis_menu import analysis_menu
from ichor.cli.sub_menus.molecular_dynamics_menu.molecular_dynamics_menu import molecular_dynamics_menu
from ichor.cli.sub_menus.tools_menu.tools_menu import tools_menu
from ichor.cli.menu_descriptions import POINTS_DIRECTORY_MENU_DESCRIPTION, MOLECULAR_DYNAMICS_MENU_DESCRIPTION, \
    TOOLS_MENU_DESCRIPTION, ANALYSIS_MENU_DESCRIPTION, MAIN_MENU_DESCRIPTION

# Create the menu
main_menu = ConsoleMenu(MAIN_MENU_DESCRIPTION.title, prologue_text=MAIN_MENU_DESCRIPTION.prologue_text)

# A SubmenuItem lets you add a menu (the selection_menu above, for example)
# as a submenu of another menu
submenu_item1 = SubmenuItem(POINTS_DIRECTORY_MENU_DESCRIPTION.title, points_directory_menu, main_menu)
submenu_item2 = SubmenuItem(ANALYSIS_MENU_DESCRIPTION.title, analysis_menu, main_menu)
submenu_item3 = SubmenuItem(MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title, molecular_dynamics_menu, main_menu)
submenu_item4 = SubmenuItem(TOOLS_MENU_DESCRIPTION.title, tools_menu, main_menu)

main_menu.append_item(submenu_item1)
main_menu.append_item(submenu_item2)
main_menu.append_item(submenu_item3)
main_menu.append_item(submenu_item4)

def run_main_menu():
    """ Runs main ichor menu."""
    main_menu.show()
