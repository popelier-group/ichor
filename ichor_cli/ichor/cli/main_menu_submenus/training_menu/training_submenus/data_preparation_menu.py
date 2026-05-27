from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_float,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.hpc.main.polus import submit_polus, write_dataset_prep


AVAILABLE_PROPS = {
    "iqa": "iqa",
    "q00": "q00",
    "q10": "q10",
    "q11c": "q11c",
    "q11s": "q11s",
    "q20": "q20",
    "q21s": "q21s",
    "q21c": "q21c",
    "q22s": "q22s",
    "q22c": "q22c",
}

SUBMIT_DATA_PREP_MENU_DESCRIPTION = MenuDescription(
    "Dataset Preparation Menu",
    subtitle="Use this menu to prepare datasets for training.\n",
)

SUBMIT_DATA_PREP_MENU_DEFAULTS = {
    "default_ncores": 2,
    "default_props": ["iqa"],
    "default_q00_threshold": 0.005,
    "default_train_size": [1000],
    "default_val_size": 250,
    "default_test_size": 1000,
}


# dataclass used to store values for submit dataset preparation menu
@dataclass
class SubmitDataPrepMenuOptions(MenuOptions):
    selected_input_directory_path: Path
    selected_number_of_cores: int
    selected_props: str
    selected_q00_threshold: float
    selected_train_size: int
    selected_val_size: int
    selected_test_size: int

    def check_path(self):

        input_directory_path = Path(self.selected_input_directory_path)
        if not input_directory_path.is_dir():
            return "Current path is not a directory."


# initialize dataclass for storing information for menu
submit_data_prep_menu_options = SubmitDataPrepMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH,
    *SUBMIT_DATA_PREP_MENU_DEFAULTS.values(),
)


# class with static methods for each menu item that calls a function.
class SubmitDataPrepFunctions:
    @staticmethod
    def select_input_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path("Change Directory Path: ")
        ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_data_prep_menu_options.selected_input_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to select the number of cores."""
        submit_data_prep_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_data_prep_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_props():
        """Asks user to select the number of properties to train on."""
        number_of_props = user_input_int(
            "Enter number of properties to train on: ",
        )

        props = []

        for prop in range(1, number_of_props + 1):
            props.append(
                user_input_restricted(
                    AVAILABLE_PROPS.keys(),
                    f"Enter property {prop}: ",
                )
            )

        submit_data_prep_menu_options.selected_props = props

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Properties for training: {submit_data_prep_menu_options.selected_props}."
        )

    @staticmethod
    def select_q00_threshold():
        """Asks user to select the recovery test filter threshold for q00."""
        submit_data_prep_menu_options.selected_q00_threshold = user_input_float(
            "Enter filter threshold: ",
            submit_data_prep_menu_options.selected_q00_threshold,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Data prep sample pool size {submit_data_prep_menu_options.selected_q00_threshold}"
        )

    @staticmethod
    def select_train_size():
        """Asks user to select the size of the training set for machine learning."""
        number_of_training_sets = user_input_int(
            "Enter number of training sets: ",
        )

        training_set_sizes = []

        for train_set in range(1, number_of_training_sets + 1):
            training_set_sizes.append(
                user_input_int(f"Enter training set size {train_set}: ")
            )

        submit_data_prep_menu_options.selected_train_size = training_set_sizes

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Training set size(s) {submit_data_prep_menu_options.selected_train_size}"
        )

    @staticmethod
    def select_val_size():
        """Asks user to select the size of the validation set for testing."""
        submit_data_prep_menu_options.selected_val_size = user_input_int(
            "Enter valiation set size: ",
            submit_data_prep_menu_options.selected_val_size,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Validation set size {submit_data_prep_menu_options.selected_val_size}"
        )

    @staticmethod
    def select_test_size():
        """Asks user to select the size of the test set for machine learning."""
        submit_data_prep_menu_options.selected_test_size = user_input_int(
            "Enter test set size: ",
            submit_data_prep_menu_options.selected_test_size,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Test set size {submit_data_prep_menu_options.selected_q00_threshold}"
        )

    @staticmethod
    def submit_data_prep_on_compute():
        """Submits polus job for data preparation."""
        (ncores, props, q00_threshold, train_size, val_size, test_size) = (
            submit_data_prep_menu_options.selected_number_of_cores,
            submit_data_prep_menu_options.selected_props,
            submit_data_prep_menu_options.selected_q00_threshold,
            submit_data_prep_menu_options.selected_train_size,
            submit_data_prep_menu_options.selected_val_size,
            submit_data_prep_menu_options.selected_test_size,
        )

        input_path = Path(ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH)

        _ = write_dataset_prep(
            outlier_input_dir=input_path,
            q00_threshold=q00_threshold,
            props=props,
            train_size=train_size,
            val_size=val_size,
            test_size=test_size,
        )

        submit_polus(
            input_script="dataset_split.py",
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES["datasets"],
            cwd=Path(ichor.hpc.global_variables.FILE_STRUCTURE["datasets"]).resolve(),
            ncores=ncores,
        )

        SUBMIT_DATA_PREP_MENU_DESCRIPTION.prologue_description_text = (
            "Successfully submitted data preparation \n"
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            "Data preparation for machine learning job submitted"
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_data_prep_menu_items = [
    FunctionItem(
        "Select input directory",
        SubmitDataPrepFunctions.select_input_directory,
    ),
    FunctionItem(
        "Change cores",
        SubmitDataPrepFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change properties",
        SubmitDataPrepFunctions.select_props,
    ),
    FunctionItem(
        "Change q00 threshold",
        SubmitDataPrepFunctions.select_q00_threshold,
    ),
    FunctionItem(
        "Change train set size",
        SubmitDataPrepFunctions.select_train_size,
    ),
    FunctionItem(
        "Change val set size",
        SubmitDataPrepFunctions.select_val_size,
    ),
    FunctionItem(
        "Change test set size",
        SubmitDataPrepFunctions.select_test_size,
    ),
    FunctionItem(
        "Submit data prep sampler",
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
