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

AVAILABLE_READ_FILE_FORMATS = []

AVAILABLE_WRITE_FILE_FORMATS = [
    "abinit-in",
    "aims",
    "bundletrajectory",
    "castep-cell",
    "castep-geom",
    "castep-md",
    "cfg",
    "cif",
    "crystal",
    "cube",
    "db",
    "dftb",
    "dlp4",
    "dmol-arc",
    "dmol-car",
    "dmol-incoor",
    "elk-in",
    "eon",
    "eps",
    "espresso-in",
    "extxyz",
    "findsym",
    "gamess-us-in",
    "gaussian-in",
    "gen",
    "gif",
    "gpumd",
    "gromacs",
    "gromos",
    "html",
    "json",
    "jsv",
    "lammps-data",
    "magres",
    "mp4",
    "mustem",
    "mysql",
    "netcdftrajectory",
    "nwchem-in",
    "onetep-in",
    "png",
    "postgresql",
    "pov",
    "prismatic",
    "proteindatabank",
    "py",
    "res",
    "rmc6f",
    "struct",
    "sys",
    "traj",
    "turbomole",
    "v-sim",
    "vasp",
    "vasp-xdatcar",
    "vti",
    "vtu",
    "x3d",
    "xsd",
    "xsf",
    "xtd",
    "xyz",
]

INITIAL_STRUCTURE_MENU_DESCRIPTION = MenuDescription(
    "Initial Structure Menu",
    subtitle="Hello hello hello.\n",
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
    # SubmenuItem(
    #    "Set path to geometry for checking.",
    #    InitialStructureMenuFunctions.select_xyz,
    # ),
]

add_items_to_menu(initial_structure_menu, initial_structure_menu_items)
