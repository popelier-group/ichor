from dataclasses import dataclass

from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import print_summary_and_pause

FFLUX_API_MENU_DESCRIPTION = MenuDescription(
    "FFLUX_API Menu",
    subtitle="Set up and run FFLUX calculations via the FFLUX API.",
)


# this menu currently holds no options; it is a placeholder to be filled in later
@dataclass
class FFLUXAPIMenuOptions(MenuOptions):
    pass


fflux_api_menu_options = FFLUXAPIMenuOptions()


class FFLUXAPIMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def placeholder():
        """Placeholder for the FFLUX_API functionality, which is not yet implemented."""
        print_summary_and_pause(
            "FFLUX_API NOT IMPLEMENTED YET",
            notes=[
                "This menu is a placeholder for running FFLUX calculations through the "
                "FFLUX API, and nothing has been set up or submitted.",
                "To run FFLUX calculations in the meantime, use the DL_FFLUX menu, "
                "which sets up and submits FFLUX-based DL_POLY runs.",
            ],
        )


# initialize menu
fflux_api_menu = ConsoleMenu(
    this_menu_options=fflux_api_menu_options,
    title=FFLUX_API_MENU_DESCRIPTION.title,
    subtitle=FFLUX_API_MENU_DESCRIPTION.subtitle,
    prologue_text=FFLUX_API_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=FFLUX_API_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=FFLUX_API_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
fflux_api_menu_items = [
    FunctionItem(
        "FFLUX_API setup (placeholder - not yet implemented)",
        FFLUXAPIMenuFunctions.placeholder,
    ),
]

add_items_to_menu(fflux_api_menu, fflux_api_menu_items)
