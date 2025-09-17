from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_restricted, user_input_int
from ichor.hpc.main.polus import submit_polus, write_diversity_sampling


SUBMIT_DATA_PREP_MENU_DESCRIPTION = MenuDescription(
    "Dataset Preparation Menu",
    subtitle="Use this menu to repare datasets for training.\n",
)

SUBMIT_DATA_PREP_MENU_DEFAULTS = {
    "default_ncores": 2,
    "default_outlier_method": "extrZS",
    "default_q00_threshold": 0.005,
    "default_train_size": [1000],
    "default_val_size": [250],
    "default_test_size": [1000],
}


# dataclass used to store values for submit dataset preparation menu
@dataclass
class SubmitDataPrepMenuOptions(MenuOptions):
        # defaults to the current working directory
    selected_points_directory_path: Path

    def check_path(self):

        input_data_path = Path(self.selected_points_directory_path)
        if not input_data_path.is_dir():
            return "Current path is not a directory."


    selected_ncores: int
    selected_outlier_method:str
    selected_q00_threshold: int
    selected_train_size: int
    selected_val_size: int
    selected_test_size: int


# initialize dataclass for storing information for menu
submit_data_prep_menu_options = SubmitDataPrepMenuOptions(
    *SUBMIT_DATA_PREP_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitDataPrepFunctions:
    @staticmethod
    def select_number_of_cores():
        """Asks user to select the number of cores."""
        submit_data_prep_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_data_prep_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_outlier_method():
        """Asks user to select method for outliers"""
        submit_data_prep_menu_options.selected_outlier_method = user_input_restricted(
            "Enter outlier removal method: ",
            submit_data_prep_menu_options.selected_outlier_method,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Dataset outliers removed using {submit_data_prep_menu_options.selected_outlier_method} method."
        )

    @staticmethod
    def select_q00_threshold():
        """Asks user to select the recovery test filter threshold for q00."""
        submit_data_prep_menu_options.selected_q00_threshold = user_input_int(
            "Enter filter threshold: ",
            submit_data_prep_menu.selected_q00_threshold,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"data_prep sample pool size {submit_data_prep_menu_options.selected_q00_threshold}"
        )

    @staticmethod
    def submit_data_prep_on_compute():
        """Submits polus job for data preparation."""
        (ncores, weights, sample_size,) = (
            submit_data_prep_menu_options.selected_ncores,
            submit_data_prep_menu_options.selected_outlier_method,
            submit_data_prep_menu_options.selected_q00_threshold,
        )

        if not weights:
            weights_vector = "HL1:1"
        else:
            weights_vector = "HL1:0"

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)
        trajectory_path = Path(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)

        div_script = write_diversity_sampling(
            filename=trajectory_path,
            seed_geom=xyz_path,
            weights_vector=weights_vector,
            sample_size=sample_size,
        )

        submit_polus(
            input_script=div_script,
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES[
            "data_prep_sampling"],
            ncores=ncores,
        )

        SUBMIT_DATA_PREP_MENU_DESCRIPTION.prologue_description_text = (
            "Successfully submitted data_prep sampling \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"data_prep sampling job submitted for {xyz_path}"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_data_prep_menu_items = [
    FunctionItem(
        "Change cores",
        SubmitDataPrepFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change weights",
        SubmitDataPrepFunctions.select_weights,
    ),
    FunctionItem(
        "Change sample size",
        SubmitDataPrepFunctions.select_sample_size,
    ),
    FunctionItem(
        "Submit data_prep sampler",
        SubmitDataPrepFunctions.submit_data_prep_on_compute,
    ),
]

# initialize menu
submit_data_prep_menu = ConsoleMenu(
    this_menu_options=submit_data_prep_menu_options,
    title=SUBMIT_DATA_PREP_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_DATA_PREP_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_DATA_PREP_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_DATA_PREP_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_DATA_PREP_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_data_prep_menu, submit_data_prep_menu_items)
