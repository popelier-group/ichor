from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.initial_structure_menu.initial_structure_submenus import (
    file_conversion_menu,
    FILE_CONVERSION_MENU_DESCRIPTION,
    optimisation_menu,
    OPTIMISATION_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription

INITIAL_STRUCTURE_MENU_DESCRIPTION = MenuDescription(
    "Initial Structure Menu",
    subtitle="Hello hello hello.\n",
)

# initialize menu
initial_structure_menu = ConsoleMenu(
    title=INITIAL_STRUCTURE_MENU_DESCRIPTION.title,
    subtitle=INITIAL_STRUCTURE_MENU_DESCRIPTION.subtitle,
    prologue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=INITIAL_STRUCTURE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=INITIAL_STRUCTURE_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
initial_structure_menu_items = [
    SubmenuItem(
        FILE_CONVERSION_MENU_DESCRIPTION.title,
        file_conversion_menu,
        initial_structure_menu,
    ),
    SubmenuItem(
        OPTIMISATION_MENU_DESCRIPTION.title, optimisation_menu, initial_structure_menu
    ),
    # SubmenuItem(
    #    "Set path to geometry for checking.",
    #    InitialStructureMenuFunctions.select_xyz,
    # ),
]

add_items_to_menu(initial_structure_menu, initial_structure_menu_items)
