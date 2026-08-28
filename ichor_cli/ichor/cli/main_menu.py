from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.hpc.global_variables

from consolemenu.items import SubmenuItem
from ichor.cli.completers import install_completion_interrupt_handler
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.analysis_menu import (
    analysis_menu,
    ANALYSIS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.fflux_calculations_menu import (
    fflux_calculations_menu,
    FFLUX_CALCULATIONS_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.initial_structure_menu import (
    initial_structure_menu,
    INITIAL_STRUCTURE_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.points_directory_menu import (
    points_directory_menu,
    POINTS_DIRECTORY_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.sampling_menu import (
    sampling_menu,
    SAMPLING_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.training_menu.training_menu import (
    training_menu,
    TRAINING_MENU_DESCRIPTION,
)
from ichor.cli.main_menu_submenus.trajectory_creation_menu.trajectory_creation_menu import (
    trajectory_creation_menu,
    TRAJECTORY_CREATION_MENU_DESCRIPTION,
)

from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.hpc.config_file import config_search_locations


@dataclass
class MainMenuMenuOptions(MenuOptions):
    # the config file ichor.hpc found, or None if there is not one yet
    selected_ichor_config_file: Union[Path, None]

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether a config file was found in any of the locations ichor
        looks in, as the menu system cannot submit anything without one."""
        if self.selected_ichor_config_file is None:
            searched = "\n".join(
                f"  {location}" for location in config_search_locations()
            )
            return (
                "No ichor config file was found, it is required to use the menu "
                "system.\nRun `ichor-config-init` to create one, then edit it for "
                f"the machine you are on.\nSearched, in order:\n{searched}"
            )
        if not self.selected_ichor_config_file.exists():
            return (
                f"The config file {self.selected_ichor_config_file} no longer exists!"
                "\nIt is required to use the menu system."
            )


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
    SubmenuItem(SAMPLING_MENU_DESCRIPTION.title, sampling_menu, main_menu),
    SubmenuItem(
        POINTS_DIRECTORY_MENU_DESCRIPTION.title, points_directory_menu, main_menu
    ),
    SubmenuItem(TRAINING_MENU_DESCRIPTION.title, training_menu, main_menu),
    SubmenuItem(
        FFLUX_CALCULATIONS_MENU_DESCRIPTION.title,
        fflux_calculations_menu,
        main_menu,
    ),
    SubmenuItem(ANALYSIS_MENU_DESCRIPTION.title, analysis_menu, main_menu),
]

# add items to menu
add_items_to_menu(main_menu, main_menu_items)


# this function will be used by setuptools entry points
def run_main_menu():
    """Runs main ichor menu."""
    # must be done from the main thread, before the menu loop is started in its
    # own thread, so that Ctrl+C cancels a slow Tab completion instead of
    # taking down the whole menu
    install_completion_interrupt_handler()
    main_menu.show()
