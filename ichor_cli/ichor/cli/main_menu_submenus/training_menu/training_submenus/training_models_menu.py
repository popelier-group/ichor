from dataclasses import dataclass

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_int, user_input_restricted, user_input_float

from ichor.hpc.main import submit_pyferebus, write_pyferebus_input_script

AVAILABLE_MEAN_TYPES = {
    "physical": 15,
}

AVAILABLE_KERNEL_TYPES = {
    "rbfc_per": "rbfc_per",
}

SUBMIT_TRAINING_MENU_DESCRIPTION = MenuDescription(
    "Model Training Menu",
    subtitle="Use this menu to train your GPR models.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_TRAINING_MENU_DEFAULTS = {
    "default_ncores": 2,
    "default_kernel": "rbfc_per",
    "default_max_iter": 100,
    "default_huber_delta": 0.05,
    "default_mean_type": "physical",
    "default_gwo_cycles": 1.0,
}


# dataclass used to store values for SubmitTrainingLMenu
@dataclass
class SubmitTrainingMenuOptions(MenuOptions):

    selected_number_of_cores: str
    selected_kernel: str
    selected_max_iter: int
    selected_huber_delta: float
    selected_mean_type: str
    selected_gwo_cycles: float


# initialize dataclass for storing information for menu
submit_training_menu_options = SubmitTrainingMenuOptions(
    *SUBMIT_TRAINING_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitTrainingFunctions:
    @staticmethod
    def select_number_of_cores():
        """Asks user to select number of cores."""
        submit_training_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_training_menu_options.selected_number_of_cores,
        )
    
    @staticmethod
    def select_kernel():
        """Asks user to select kernel."""
        submit_training_menu_options.selected_kernel = user_input_restricted(
            AVAILABLE_KERNEL_TYPES.keys(),
            "Enter kernel type: ",
            submit_training_menu_options.selected_kernel,
        )

    @staticmethod
    def select_max_iter():
        """Asks user to select max iterations."""
        submit_training_menu_options.selected_max_iter = user_input_int(
            "Enter number of max iterations: ",
            submit_training_menu_options.selected_max_iter,
        )
    
    @staticmethod
    def select_huber_delta():
        """Asks user to select huber delta."""
        submit_training_menu_options.selected_huber_delta = user_input_float(
            "Enter huber delta: ",
            submit_training_menu_options.selected_huber_delta,
        )
    
    @staticmethod
    def select_mean_type():
        """Asks user to select mean type."""
        submit_training_menu_options.selected_mean_type = user_input_restricted(
            AVAILABLE_MEAN_TYPES.keys(),
            "Enter mean type: ",
            submit_training_menu_options.selected_mean_type,
        )

    @staticmethod
    def select_gwo_cycles():
        """Asks user to select gwo cycles."""
        submit_training_menu_options.selected_gwo_cycles = user_input_float(
            "Enter gwo cycles: ",
            submit_training_menu_options.gwo_cycles,
        )

    @staticmethod
    def submit_training_on_compute():
        """Creates and submits models for training."""
        (
            ncores,
            kernel,
            max_iter,
            huber_delta,
            mean_type,
            gwo_cycles,
        ) = (
            submit_training_menu_options.selected_number_of_cores,
            submit_training_menu_options.selected_kernel,
            submit_training_menu_options.selected_max_iter,
            submit_training_menu_options.selected_huber_delta,
            submit_training_menu_options.selected_mean_type,
            submit_training_menu_options.selected_gwo_cycles,
        )

        pyferebus_input_script = write_pyferebus_input_script(           
            kernel=kernel,
            max_iter=max_iter,
            huber_delta=huber_delta,
            mean_type=mean_type,
            gwo_cycles=gwo_cycles,
        )

        submit_pyferebus(
            input_script=pyferebus_input_script,
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES["training_models"],
            ncores=ncores,
        )

        SUBMIT_TRAINING_MENU_DESCRIPTION.prologue_description_text = (
            "Successfully submitted models for trianing \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Training model job submitted"
        )




# make menu items
# can use lambda functions to change text of options as well :)
submit_training_menu_items = [
    FunctionItem(
        "Change number of cores",
        SubmitTrainingFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change kernel type",
        SubmitTrainingFunctions.select_kernel,
    ),
    FunctionItem(
        "Change max iterations",
        SubmitTrainingFunctions.select_max_iter,
    ),
    FunctionItem(
        "Change huber delta",
        SubmitTrainingFunctions.select_huber_delta,
    ),
    FunctionItem(
        "Change mean type",
        SubmitTrainingFunctions.select_mean_type,
    ),
    FunctionItem(
        "Change gwo cycles",
        SubmitTrainingFunctions.select_gwo_cycles,
    ),
    FunctionItem(
        "Submit for training",
        SubmitTrainingFunctions.submit_training_on_compute,
    ),
]

# initialize menu
submit_training_menu = ConsoleMenu(
    this_menu_options=submit_training_menu_options,
    title=SUBMIT_TRAINING_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_TRAINING_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_TRAINING_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_TRAINING_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_TRAINING_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_training_menu, submit_training_menu_items)
