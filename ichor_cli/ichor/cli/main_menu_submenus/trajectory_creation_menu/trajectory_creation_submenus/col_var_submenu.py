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

# TODO: possibly make this be read from a file
COL_VAR_MENU_DEFAULTS = {
    "default_timestep": 0.005,
    "default_bias_factor": 5,
    "default_number_of_iterations": 1024,
    "default_temperature": 300,
    "default_calculator": "GFN2-xTB",
}

COL_VAR_MENU_DESCRIPTION = MenuDescription(
    "Collective Variable Menu",
    subtitle="Use this menu to define collective variables for metadynamics calculations with ASE/PLUMED.",
)


@dataclass
class ColVarMenuOptions(MenuOptions):

    selected_timestep: float
    selected_bias: float
    selected_number_of_iterations: int
    selected_temperature: float
    selected_calculator: str


col_var_menu_options = ColVarMenuOptions(*COL_VAR_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class ColVarMenuFunctions:

    @staticmethod
    def select_timestep():
        """
        Select timestep for metadynamics simulation.
        """
        col_var_menu_options.selected_timestep = user_input_float(
            "Select timestep (fs): ", col_var_menu_options.selected_timestep
        )

    @staticmethod
    def select_bias_factor():
        """
        Selects bias factor for collective variables in a metadynamics simulation.
        """
        col_var_menu_options.selected_bias = user_input_float(
            "Select bias factor: ",
            col_var_menu_options.selected_bias,
        )

    @staticmethod
    def select_number_of_iterations():
        """
        Select how many iterations to run for in metadynamics simulation.
        """
        col_var_menu_options.selected_number_of_iterations = user_input_int(
            "Set number of simulation iterations: ",
            col_var_menu_options.selected_number_of_iterations,
        )

    @staticmethod
    def select_temperature():
        """
        Set the temperature for metadynamics calculation.
        """
        col_var_menu_options.selected_temperature = user_input_float(
            "Selected temperature (K): ", col_var_menu_options.selected_temperature
        )

    @staticmethod
    def select_calculator():
        """
        Select the calculator to use for metadynamics.
        """
        col_var_menu_options.selected_calculator = user_input_free_flow(
            "Select calculator: ", col_var_menu_options.selected_calculator
        )


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
        "Select timestep (fs)",
        ColVarMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select bias factor for collective variables",
        ColVarMenuFunctions.select_bias_factor,
    ),
    FunctionItem(
        "Select number of iterations",
        ColVarMenuFunctions.select_number_of_iterations,
    ),
    FunctionItem(
        "Select simulation temperature (K)",
        ColVarMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select calculator to use for metadynamics",
        ColVarMenuFunctions.select_calculator,
    ),
]

add_items_to_menu(col_var_menu, col_var_menu_items)
