from dataclasses import dataclass

from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.fflux_calculations_menu.fflux_calculations_submenus import (  # noqa: E501
    dl_fflux_condensed_menu,
    DL_FFLUX_CONDENSED_MENU_DESCRIPTION,
    dl_fflux_menu,
    DL_FFLUX_MENU_DESCRIPTION,
    extract_history_menu,
    EXTRACT_HISTORY_MENU_DESCRIPTION,
    fflux_api_menu,
    FFLUX_API_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions

FFLUX_CALCULATIONS_MENU_DESCRIPTION = MenuDescription(
    "FFLUX Calculations Menu",
    subtitle="Use this to set up and run FFLUX calculations.",
)


# the FFLUX calculations menu itself holds no options; each calculation type has its
# own submenu with its own options
@dataclass
class FFLUXCalculationsMenuOptions(MenuOptions):
    pass


# initialize dataclass for storing information for menu
fflux_calculations_menu_options = FFLUXCalculationsMenuOptions()


fflux_calculations_menu = ConsoleMenu(
    this_menu_options=fflux_calculations_menu_options,
    title=FFLUX_CALCULATIONS_MENU_DESCRIPTION.title,
    subtitle=FFLUX_CALCULATIONS_MENU_DESCRIPTION.subtitle,
    prologue_text=FFLUX_CALCULATIONS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=FFLUX_CALCULATIONS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=FFLUX_CALCULATIONS_MENU_DESCRIPTION.show_exit_option,
)


# make menu items
fflux_calculations_menu_items = [
    SubmenuItem(
        FFLUX_API_MENU_DESCRIPTION.title, fflux_api_menu, fflux_calculations_menu
    ),
    SubmenuItem(
        DL_FFLUX_MENU_DESCRIPTION.title, dl_fflux_menu, fflux_calculations_menu
    ),
    SubmenuItem(
        DL_FFLUX_CONDENSED_MENU_DESCRIPTION.title,
        dl_fflux_condensed_menu,
        fflux_calculations_menu,
    ),
    SubmenuItem(
        EXTRACT_HISTORY_MENU_DESCRIPTION.title,
        extract_history_menu,
        fflux_calculations_menu,
    ),
]

add_items_to_menu(fflux_calculations_menu, fflux_calculations_menu_items)
