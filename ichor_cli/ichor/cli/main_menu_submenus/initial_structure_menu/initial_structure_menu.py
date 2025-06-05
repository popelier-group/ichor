from dataclasses import dataclass

from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.initial_structure_menu.initial_structure_submenus import (
    file_conversion_menu,
    FILE_CONVERSION_MENU_DESCRIPTION,
    optimisation_menu,
    OPTIMISATION_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions

INITIAL_STRUCTURE_MENU_DESCRIPTION = MenuDescription(
    "Initial Structure Menu",
    subtitle="This menu is designed for generating your initial xyz file for building ML models.\n",
)


@dataclass
class InitialStructureMenuOptions(MenuOptions):
    pass


# initialize dataclass for storing information for menu
initial_structure_menu_options = InitialStructureMenuOptions()


# initialize menu
initial_structure_menu = ConsoleMenu(
    this_menu_options=initial_structure_menu_options,
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
]

add_items_to_menu(initial_structure_menu, initial_structure_menu_items)
