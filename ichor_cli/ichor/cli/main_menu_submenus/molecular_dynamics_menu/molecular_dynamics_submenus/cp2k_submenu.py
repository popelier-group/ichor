from dataclasses import dataclass

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_free_flow, user_input_int
from ichor.hpc.molecular_dynamics import submit_cp2k

# TODO: possibly make this be read from a file
CP2K_MENU_DEFAULTS = {
    "default_method": "BLYP",
    "default_basis_set": "6-31G*",
    "default_temperature": 300,
    "default_nsteps": 10_000,
    "default_molecular_charge": 0,
    "default_spin_multiplicity": 1,
    "default_number_of_cores": 8,
}

CP2K_MENU_DESCRIPTION = MenuDescription(
    "CP2K Menu", subtitle="Use this to submit CP2K simulations."
)


@dataclass
class CP2KMenuOptions(MenuOptions):

    selected_method: str
    selected_basis_set: str
    selected_temperature: int
    selected_number_of_timesteps: int
    selected_molecular_charge: int
    selected_spin_multiplicity: int
    selected_number_of_cores: int


cp2k_menu_options = CP2KMenuOptions(*CP2K_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class CP2KMenuFunctions:
    @staticmethod
    def select_method():
        """
        Select the method used by CP2K.
        """
        cp2k_menu_options.selected_method = user_input_free_flow(
            "Select method: ", cp2k_menu_options.selected_method
        )

    @staticmethod
    def select_basis_set():
        """
        Select basis set used by CP2K.
        """
        cp2k_menu_options.selected_basis_set = user_input_free_flow(
            "Select basis set: ", cp2k_menu_options.selected_basis_set
        )

    @staticmethod
    def select_temperature():
        """
        Select temperature of CP2K simulation.
        """
        cp2k_menu_options.selected_temperature = user_input_int(
            "Select temperature: ", cp2k_menu_options.selected_temperature
        )

    @staticmethod
    def select_number_of_timesteps():
        """
        Selects the number of timesteps in CP2K simulation.
        """
        cp2k_menu_options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps:",
            cp2k_menu_options.selected_number_of_timesteps,
        )

    @staticmethod
    def select_molecular_charge():
        """
        Select molecular charge of CP2K.
        """
        cp2k_menu_options.selected_molecular_charge = user_input_int(
            "Select molecular charge:", cp2k_menu_options.selected_molecular_charge
        )

    @staticmethod
    def select_spin_multiplicity():
        """
        Select the spin multiplicty used by CP2K.
        """
        cp2k_menu_options.selected_spin_multiplicity = user_input_int(
            "Selected spin multiplicity: ", cp2k_menu_options.selected_spin_multiplicity
        )

    @staticmethod
    def select_numer_of_cores():
        """
        Select the number of cores to use for CP2K.
        """
        cp2k_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ", cp2k_menu_options.selected_number_of_cores
        )

    @staticmethod
    def submit_cp2k_to_compute():
        """Submits CP2K job to compute node with the given settings."""

        method = cp2k_menu_options.selected_method
        basis_set = cp2k_menu_options.selected_basis_set
        temperature = cp2k_menu_options.selected_temperature
        nsteps = cp2k_menu_options.selected_number_of_timesteps
        molecular_charge = cp2k_menu_options.selected_molecular_charge
        spin_multiplicity = cp2k_menu_options.selected_spin_multiplicity
        ncores = cp2k_menu_options.selected_number_of_cores

        submit_cp2k(
            input_file=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            system_name=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH.stem,
            temperature=temperature,
            nsteps=nsteps,
            method=method,
            basis_set=basis_set,
            molecular_charge=molecular_charge,
            spin_multiplicity=spin_multiplicity,
            ncores=ncores,
        )


# initialize menu
cp2k_menu = ConsoleMenu(
    this_menu_options=cp2k_menu_options,
    title=CP2K_MENU_DESCRIPTION.title,
    subtitle=CP2K_MENU_DESCRIPTION.subtitle,
    prologue_text=CP2K_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=CP2K_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=CP2K_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
cp2k_menu_items = [
    FunctionItem(
        "Select method",
        CP2KMenuFunctions.select_method,
    ),
    FunctionItem(
        "Select basis set",
        CP2KMenuFunctions.select_basis_set,
    ),
    FunctionItem(
        "Select simulation temperature",
        CP2KMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select number of timesteps",
        CP2KMenuFunctions.select_number_of_timesteps,
    ),
    FunctionItem(
        "Select molecular charge",
        CP2KMenuFunctions.select_molecular_charge,
    ),
    FunctionItem(
        "Select spin multiplicity",
        CP2KMenuFunctions.select_spin_multiplicity,
    ),
    FunctionItem(
        "Select number of cores",
        CP2KMenuFunctions.select_numer_of_cores,
    ),
    FunctionItem(
        "Submit CP2K Job to Compute",
        CP2KMenuFunctions.submit_cp2k_to_compute,
    ),
]

add_items_to_menu(cp2k_menu, cp2k_menu_items)
