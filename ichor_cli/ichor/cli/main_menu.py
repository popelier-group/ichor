from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.hpc.global_variables

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
from ichor.cli.main_menu_submenus.initial_structure_menu import (
    initial_structure_menu,
    INITIAL_STRUCTURE_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.trajectory_creation_menu.trajectory_creation_menu import (
    trajectory_creation_menu,
    TRAJECTORY_CREATION_MENU_DESCRIPTION,
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


@dataclass
class MainMenuMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_ichor_config_file: Path

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the ichor_config.yaml is present in the user home directory."""
        if not self.selected_ichor_config_file.exists():
            return "The ichor_config.yaml file is not in the home directory!\nIt is required to use the menu system."


# initialize dataclass for storing information for menu
main_menu_menu_options = MainMenuMenuOptions(
    ichor.hpc.global_variables.ICHOR_CONFIG_PATH
)

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
        INITIAL_STRUCTURE_MENU_DESCRIPTION.title, initial_structure_menu, main_menu
    ),
    SubmenuItem(
        TRAJECTORY_CREATION_MENU_DESCRIPTION.title, trajectory_creation_menu, main_menu
    ),
    SubmenuItem(TRAJECTORY_MENU_DESCRIPTION.title, trajectory_menu, main_menu),
    SubmenuItem(
        POINTS_DIRECTORY_MENU_DESCRIPTION.title, points_directory_menu, main_menu
    ),
    SubmenuItem(SUBMIT_CSVS_MENU_DESCRIPTION.title, submit_csvs_menu, main_menu),
    SubmenuItem(ANALYSIS_MENU_DESCRIPTION.title, analysis_menu, main_menu),
    SubmenuItem(TOOLS_MENU_DESCRIPTION.title, tools_menu, main_menu),
]

# add items to menu
add_items_to_menu(main_menu, main_menu_items)


# this function will be used by setuptools entry points
def run_main_menu():
    """Runs main ichor menu."""
    main_menu.show()
