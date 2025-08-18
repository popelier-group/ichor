from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_float,
    user_input_free_flow,
    user_input_int,
)
from ichor.cli.main_menu_submenus.trajectory_creation_menu.trajectory_creation_submenus.col_var_submenu import (
    col_var_menu,
    COL_VAR_MENU_DESCRIPTION,
)
from ichor.hpc.molecular_dynamics import submit_metadynamics

# TODO: possibly make this be read from a file
METADYNAMICS_MENU_DEFAULTS = {
    "default_timestep": 0.005,
    "default_bias_factor": 5,
    "default_number_of_iterations": 1024,
    "default_temperature": 300,
    "default_calculator": "GFN2-xTB",
}

METADYNAMICS_MENU_DESCRIPTION = MenuDescription(
    "Metadynamics Menu",
    subtitle="Use this to submit metadynamics simulations with ASE/PLUMED.",
)


@dataclass
class MetadynamicsMenuOptions(MenuOptions):

    selected_timestep: float
    selected_bias: float
    selected_number_of_iterations: int
    selected_temperature: float
    selected_calculator: str


metadynamics_menu_options = MetadynamicsMenuOptions(
    *METADYNAMICS_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class MetadynamicsMenuFunctions:

    @staticmethod
    def select_timestep():
        """
        Select timestep for metadynamics simulation.
        """
        metadynamics_menu_options.selected_timestep = user_input_float(
            "Select timestep (fs): ", metadynamics_menu_options.selected_timestep
        )

    @staticmethod
    def select_bias_factor():
        """
        Selects bias factor for collective variables in a metadynamics simulation.
        """
        metadynamics_menu_options.selected_bias = user_input_float(
            "Select bias factor: ",
            metadynamics_menu_options.selected_bias,
        )

    @staticmethod
    def select_number_of_iterations():
        """
        Select how many iterations to run for in metadynamics simulation.
        """
        metadynamics_menu_options.selected_number_of_iterations = user_input_int(
            "Set number of simulation iterations: ",
            metadynamics_menu_options.selected_number_of_iterations,
        )

    @staticmethod
    def select_temperature():
        """
        Set the temperature for metadynamics calculation.
        """
        metadynamics_menu_options.selected_temperature = user_input_float(
            "Selected temperature (K): ", metadynamics_menu_options.selected_temperature
        )

    @staticmethod
    def select_calculator():
        """
        Select the calculator to use for metadynamics.
        """
        metadynamics_menu_options.selected_calculator = user_input_free_flow(
            "Select calculator: ", metadynamics_menu_options.selected_calculator
        )

    @staticmethod
    def submit_metadynamics_to_compute():
        """Asks for user input and submits metadynamics job to compute node."""

        timestep = metadynamics_menu_options.selected_timestep
        bias = metadynamics_menu_options.selected_bias
        iterations = metadynamics_menu_options.selected_number_of_iterations
        temperature = metadynamics_menu_options.selected_temperature
        calculator = metadynamics_menu_options.selected_calculator

        submit_metadynamics(
            input_file_path=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            timestep=timestep,
            bias=bias,
            nsteps=iterations,
            temperature=temperature,
            system_name=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH.stem,
            calculator=calculator,
        )


# initialize menu
metadynamics_menu = ConsoleMenu(
    this_menu_options=metadynamics_menu_options,
    title=METADYNAMICS_MENU_DESCRIPTION.title,
    subtitle=METADYNAMICS_MENU_DESCRIPTION.subtitle,
    prologue_text=METADYNAMICS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=METADYNAMICS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=METADYNAMICS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
metadynamics_menu_items = [
    SubmenuItem(COL_VAR_MENU_DESCRIPTION.title, col_var_menu, metadynamics_menu),
    FunctionItem(
        "Select timestep (fs)",
        MetadynamicsMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select bias factor for collective variables",
        MetadynamicsMenuFunctions.select_bias_factor,
    ),
    FunctionItem(
        "Select number of iterations",
        MetadynamicsMenuFunctions.select_number_of_iterations,
    ),
    FunctionItem(
        "Select simulation temperature (K)",
        MetadynamicsMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select calculator to use for metadynamics",
        MetadynamicsMenuFunctions.select_calculator,
    ),
    FunctionItem(
        "Submit metadynamics simulation",
        MetadynamicsMenuFunctions.submit_metadynamics_to_compute,
    ),
]

add_items_to_menu(metadynamics_menu, metadynamics_menu_items)
