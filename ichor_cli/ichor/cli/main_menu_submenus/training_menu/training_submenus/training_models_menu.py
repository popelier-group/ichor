from dataclasses import dataclass

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_free_flow, user_input_int
from ichor.core.files import PointsDirectory
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main import submit_points_directory_to_aimall

SUBMIT_TRAINING_MENU_DESCRIPTION = MenuDescription(
    "Model Training Menu",
    subtitle="Use this menu to train your GPR models.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_TRAINING_MENU_DEFAULTS = {
    "default_method": "b3lyp",
    "default_ncores": 2,
    "default_naat": 1,
    "default_encomp": 3,
}


# dataclass used to store values for SubmitTrainingLMenu
@dataclass
class SubmitTrainingMenuOptions(MenuOptions):

    selected_method: str
    selected_number_of_cores: str
    selected_naat: int
    selected_encomp: bool


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


# make menu items
# can use lambda functions to change text of options as well :)
submit_training_menu_items = [
    FunctionItem(
        "Change number of cores",
        SubmitTrainingFunctions.select_number_of_cores,
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
