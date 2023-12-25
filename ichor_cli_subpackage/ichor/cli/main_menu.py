from dataclasses import dataclass

from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.analysis_menu import (
    analysis_menu,
    ANALYSIS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.database_menu.submit_csvs_from_database import (
    submit_csvs_menu,
    SUBMIT_CSVS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.molecular_dynamics_menu.molecular_dynamics_menu import (
    molecular_dynamics_menu,
    MOLECULAR_DYNAMICS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.points_directory_menu import (
    points_directory_menu,
    POINTS_DIRECTORY_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.tools_menu.tools_menu import (
    tools_menu,
    TOOLS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.trajectory_menu.trajectory_menu import (
    trajectory_menu,
    TRAJECTORY_MENU_DESCRIPTION,
)

from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions

MAIN_MENU_DESCRIPTION = MenuDescription(
    "Main Menu", subtitle="Welcome to ichor's main menu!"
)

# no main menu options for now
# note: need to have typing on classes, otherwise they will not show up in the prologue
# dataclasses need to have typing


@dataclass
class MainMenuOptions(MenuOptions):
    pass


# make instance of options
main_menu_options = MainMenuOptions()

# create main menu
main_menu = ConsoleMenu(
    this_menu_options=main_menu_options,
    title=MAIN_MENU_DESCRIPTION.title,
    subtitle=MAIN_MENU_DESCRIPTION.subtitle,
    prologue_text=MAIN_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=MAIN_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=MAIN_MENU_DESCRIPTION.show_exit_option,
)

# make submenus
main_menu_items = [
    SubmenuItem(
        POINTS_DIRECTORY_MENU_DESCRIPTION.title, points_directory_menu, main_menu
    ),
    SubmenuItem(SUBMIT_CSVS_MENU_DESCRIPTION.title, submit_csvs_menu, main_menu),
    SubmenuItem(TRAJECTORY_MENU_DESCRIPTION.title, trajectory_menu, main_menu),
    SubmenuItem(ANALYSIS_MENU_DESCRIPTION.title, analysis_menu, main_menu),
    SubmenuItem(
        MOLECULAR_DYNAMICS_MENU_DESCRIPTION.title, molecular_dynamics_menu, main_menu
    ),
    SubmenuItem(TOOLS_MENU_DESCRIPTION.title, tools_menu, main_menu),
]

# add items to menu
add_items_to_menu(main_menu, main_menu_items)


# this function will be used by setuptools entry points
def run_main_menu():
    """Runs main ichor menu."""
    main_menu.show()
