from dataclasses import dataclass

from consolemenu.items import SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.points_directory_menu.points_directory_submenus import (
    check_aimall_menu,
    CHECK_AIMALL_MENU_DESCRIPTION,
    check_gaussian_menu,
    CHECK_GAUSSIAN_MENU_DESCRIPTION,
    submit_aimall_menu,
    SUBMIT_AIMALL_MENU_DESCRIPTION,
    submit_csvs_menu,
    SUBMIT_CSVS_MENU_DESCRIPTION,
    submit_database_menu,
    SUBMIT_DATABASE_MENU_DESCRIPTION,
    submit_gaussian_menu,
    SUBMIT_GAUSSIAN_MENU_DESCRIPTION,
    traj_split_menu,
    TRAJ_SPLIT_MENU_DESCRIPTION,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions


POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription(
    "Property Calculation Menu",
    subtitle="Use this to calculate atomic properties for a set of geometries "
    "(a PointsDirectory) with Gaussian and AIMAll, to check that these calculations "
    "have finished, and to collect the results into a database.\n",
)


@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    pass


# initialize dataclass for storing information for menu
points_directory_menu_options = PointsDirectoryMenuOptions()


# initialize menu
points_directory_menu = ConsoleMenu(
    this_menu_options=points_directory_menu_options,
    title=POINTS_DIRECTORY_MENU_DESCRIPTION.title,
    subtitle=POINTS_DIRECTORY_MENU_DESCRIPTION.subtitle,
    prologue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
point_directory_menu_items = [
    SubmenuItem(
        TRAJ_SPLIT_MENU_DESCRIPTION.title,
        traj_split_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        SUBMIT_GAUSSIAN_MENU_DESCRIPTION.title,
        submit_gaussian_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        CHECK_GAUSSIAN_MENU_DESCRIPTION.title,
        check_gaussian_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        SUBMIT_AIMALL_MENU_DESCRIPTION.title, submit_aimall_menu, points_directory_menu
    ),
    SubmenuItem(
        CHECK_AIMALL_MENU_DESCRIPTION.title,
        check_aimall_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        SUBMIT_DATABASE_MENU_DESCRIPTION.title,
        submit_database_menu,
        points_directory_menu,
    ),
    SubmenuItem(
        SUBMIT_CSVS_MENU_DESCRIPTION.title,
        submit_csvs_menu,
        points_directory_menu,
    ),
]

add_items_to_menu(points_directory_menu, point_directory_menu_items)
