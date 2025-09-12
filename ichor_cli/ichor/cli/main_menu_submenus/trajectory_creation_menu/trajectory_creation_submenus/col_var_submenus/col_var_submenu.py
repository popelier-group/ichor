from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_float,
    user_input_free_flow,
    user_input_int,
)

import ichor.core.molecular_dynamics.metadynamics as mtd


COL_VAR_MENU_DEFAULTS = {
    "default_num_vars": 1,
}

COL_VAR_MENU_DESCRIPTION = MenuDescription(
    "Collective Variable Menu",
    subtitle="Use this menu to define collective variables for metadynamics calculations with ASE/PLUMED.",
)


@dataclass
class ColVarMenuOptions(MenuOptions):

    selected_num_vars: int


col_var_menu_options = ColVarMenuOptions(*COL_VAR_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class ColVarMenuFunctions:

    @staticmethod
    def show_mol_info():
        """
        Display information on atoms in molecule / system.
        """
        mtd.print_molecule_data(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

        answer = ""
        user_input_free_flow("Press enter to continue: ", answer)

    @staticmethod
    def draw_labeled_molecule():
        mtd.draw_labeled_molecule(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)

    @staticmethod
    def select_num_vars():
        """
        Select number of CVs for metadynamics simulation.
        """
        col_var_menu_options.selected_num_vars = user_input_int(
            "Select number of collective variables: ",
            col_var_menu_options.selected_num_vars,
        )
        ## some function for DISTANCE - 2 ATOMS
        ## ANGLE - 3 ATOMS
        ## DIHEDRAL - 4 ATOMS


# initialize menu
col_var_menu = ConsoleMenu(
    this_menu_options=col_var_menu_options,
    title=COL_VAR_MENU_DESCRIPTION.title,
    subtitle=COL_VAR_MENU_DESCRIPTION.subtitle,
    prologue_text=COL_VAR_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=COL_VAR_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=COL_VAR_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
col_var_menu_items = [
    FunctionItem(
        "Display system information",
        ColVarMenuFunctions.show_mol_info,
    ),
    FunctionItem(
        "Output labelled molecule image",
        ColVarMenuFunctions.draw_labeled_molecule,
    ),
    FunctionItem(
        "Select number of collective variables",
        ColVarMenuFunctions.select_num_vars,
    ),
]

add_items_to_menu(col_var_menu, col_var_menu_items)
