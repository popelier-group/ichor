from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_float,
    user_input_int,
    user_input_path,
)
from ichor.hpc.main.polus import submit_polus, write_dataset_prep

AVAILABLE_PROPS = {
    "iqa": [
        "iqa",
    ],
    "monopoles": [
        "iqa",
        "q00",
    ],
    "dipoles": [
        "iqa",
        "q00",
        "q10",
        "q11c",
        "q11s",
    ],
    "quadrupoles": [
        "iqa",
        "q00",
        "q10",
        "q11c",
        "q11s",
        "q20",
        "q21c",
        "q21s",
        "q22c",
        "q22s",
    ],
    "octupoles": [
        "iqa",
        "q00",
        "q10",
        "q11c",
        "q11s",
        "q20",
        "q21c",
        "q21s",
        "q22c",
        "q22s",
        "q30",
        "q31c",
        "q31s",
        "q32c",
        "q32s",
        "q33c",
        "q33s",
    ],
    "hexadecapoles": [
        "iqa",
        "q00",
        "q10",
        "q11c",
        "q11s",
        "q20",
        "q21c",
        "q21s",
        "q22c",
        "q22s",
        "q30",
        "q31c",
        "q31s",
        "q32c",
        "q32s",
        "q33c",
        "q33s",
        "q40",
        "q41c",
        "q41s",
        "q42c",
        "q42s",
        "q43c",
        "q43s",
        "q44c",
        "q44s",
    ],
}


def train_size_list(train_size) -> list:
    """Returns the training set sizes as a list.

    The menu holds one size to begin with and a list of them once they have been chosen,
    so this is what the checks and the summary use to treat both the same way.

    :param train_size: One size or a list of them.
    """

    if isinstance(train_size, (list, tuple)):
        return list(train_size)

    return [train_size]


def count_geometries_in_csv_directory(csv_directory: Union[Path, str]) -> int:
    """Counts the geometries in a folder of per-atom csv files, which is how many there
    are to split between the training, validation and test sets.

    Every csv in the folder holds one row per geometry (its features and the property a
    model is trained on), and every atom has the same geometries, so the rows of the first
    csv found are the count. Only that one file is read.

    :param csv_directory: The folder of csv files made by 'Make csvs from database'.
    :return: The number of geometries, or 0 if there is no csv file to count (which the
        menu checks warn about).
    """

    csv_directory = Path(csv_directory)

    try:
        # the csvs are usually written straight into the folder, but a folder of
        # per-property subfolders is also read, as that is what some of the stages write
        csv_path = next(iter(sorted(csv_directory.glob("*.csv"))), None) or next(
            iter(sorted(csv_directory.rglob("*.csv"))), None
        )
        if not csv_path:
            return 0

        with open(csv_path, "r") as csv_file:
            # every line but the header of column names is one geometry
            nlines = sum(1 for _ in csv_file)
    except OSError:
        return 0

    return max(0, nlines - 1)


SUBMIT_DATA_PREP_MENU_DESCRIPTION = MenuDescription(
    "Dataset Preparation Menu",
    subtitle="Use this menu to prepare datasets for training.\n",
)

SUBMIT_DATA_PREP_MENU_DEFAULTS = {
    "default_input": "",
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
    selected_props: list[str]
    selected_q00_threshold: float
    selected_train_size: int
    selected_val_size: int
    selected_test_size: int
    # the geometries in the selected csv files, counted when the directory is selected so
    # that the dataset sizes can be checked against what there is to take them from.
    # 0 = not known
    number_of_geometries_in_csvs: int = 0

    def check_path(self):

        input_directory_path = Path(self.selected_input_directory_path)
        if not input_directory_path.is_dir():
            return "Current path is not a directory."

    def check_selected_train_size(self) -> Union[str, None]:
        """Checks the training set sizes are positive and that there are enough geometries
        to take the largest of them from."""
        train_sizes = train_size_list(self.selected_train_size)

        if not train_sizes:
            return "No training set sizes are selected."
        if any(size < 1 for size in train_sizes):
            return f"Current training set size(s): {train_sizes} must be 1 or greater."

        ngeometries = self.number_of_geometries_in_csvs
        largest = max(train_sizes)
        if ngeometries and largest > ngeometries:
            return (
                f"Current training set size: {largest:,} is larger than the "
                f"{ngeometries:,} geometries in the csv files."
            )

    def check_selected_val_size(self) -> Union[str, None]:
        """Checks the validation set size is positive and is not larger than the number of
        geometries there are."""
        if self.selected_val_size < 1:
            return (
                f"Current validation set size: {self.selected_val_size} must be 1 or "
                "greater."
            )

        ngeometries = self.number_of_geometries_in_csvs
        if ngeometries and self.selected_val_size > ngeometries:
            return (
                f"Current validation set size: {self.selected_val_size:,} is larger "
                f"than the {ngeometries:,} geometries in the csv files."
            )

    def check_selected_test_size(self) -> Union[str, None]:
        """Checks the test set size is positive and is not larger than the number of
        geometries there are."""
        if self.selected_test_size < 1:
            return f"Current test set size: {self.selected_test_size} must be 1 or greater."

        ngeometries = self.number_of_geometries_in_csvs
        if ngeometries and self.selected_test_size > ngeometries:
            return (
                f"Current test set size: {self.selected_test_size:,} is larger than the "
                f"{ngeometries:,} geometries in the csv files."
            )

    def check_dataset_sizes_fit_the_geometries(self) -> Union[str, None]:
        """Checks that the three sets can all be taken from the geometries there are.

        The sets are drawn from the same pool without overlapping, so it is their total
        that has to fit, and it has to fit with room to spare: the outlier and q00
        recovery filters throw points out of that pool before any of it is split up."""
        ngeometries = self.number_of_geometries_in_csvs
        train_sizes = train_size_list(self.selected_train_size)
        if not ngeometries or not train_sizes:
            return None
        if self.selected_val_size < 1 or self.selected_test_size < 1:
            return None

        # each training set size is a split of its own, so it is the largest of them that
        # has to fit alongside the validation and test sets
        largest = max(train_sizes)
        needed = largest + self.selected_val_size + self.selected_test_size
        if needed <= ngeometries:
            return None

        return (
            f"The training ({largest:,}), validation ({self.selected_val_size:,}) and "
            f"test ({self.selected_test_size:,}) sets need {needed:,} geometries "
            f"between them, but there are only {ngeometries:,} in the csv files. The "
            f"job filters outliers out of those before it splits them up, so the sizes "
            f"have to add up to rather less than {ngeometries:,}."
        )


# initialize dataclass for storing information for menu
submit_data_prep_menu_options = SubmitDataPrepMenuOptions(
    *SUBMIT_DATA_PREP_MENU_DEFAULTS.values(),
)


def remaining_geometries_message(set_being_chosen: str) -> str:
    """Returns a line saying how many geometries there are and how many of them the other
    two sets have already been given, which is what is left for the set being chosen.

    :param set_being_chosen: "training", "validation" or "test".
    """

    options = submit_data_prep_menu_options
    ngeometries = options.number_of_geometries_in_csvs

    if not ngeometries:
        return (
            "The number of geometries in the csv files is not known (select the input "
            "directory above), so the size cannot be checked against it."
        )

    train_sizes = train_size_list(options.selected_train_size)
    taken = {
        "training": options.selected_val_size + options.selected_test_size,
        "validation": (max(train_sizes) if train_sizes else 0)
        + options.selected_test_size,
        "test": (max(train_sizes) if train_sizes else 0) + options.selected_val_size,
    }[set_being_chosen]

    return (
        f"The csv files hold {ngeometries:,} geometries, of which the other two sets "
        f"take {taken:,}, so up to {max(0, ngeometries - taken):,} are left for the "
        f"{set_being_chosen} set. The outlier and q00 filters throw some of them out "
        f"before the split, so leave room for that."
    )


# class with static methods for each menu item that calls a function.
class SubmitDataPrepFunctions:
    @staticmethod
    def select_input_directory():
        """Asks user for path to extracted database CSV folder."""
        pd_path = user_input_path("Change Directory Path: ")
        ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_data_prep_menu_options.selected_input_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH
        )
        # the geometries in the csv files are what the three sets are taken from, so they
        # are counted here and the sizes are checked against them
        ngeometries = count_geometries_in_csv_directory(
            ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH
        )
        submit_data_prep_menu_options.number_of_geometries_in_csvs = ngeometries

        if ngeometries:
            print(f"The csv files hold {ngeometries:,} geometries.")
        else:
            print(
                "No csv files were found in that directory, so the number of geometries "
                "to split is not known. The input directory is the folder of per-atom "
                "csv files made by 'Make csvs from database' (usually a "
                "*_processed_csvs folder)."
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

        choice_map = {
            "1": "iqa",
            "2": "monopoles",
            "3": "dipoles",
            "4": "quadrupoles",
            "5": "octupoles",
            "6": "hexadecapoles",
        }

        while True:
            choice = input(
                "Train up to which level?\n"
                "(1) Iqa energies only\n"
                "(2) + Monopoles\n"
                "(3) + Dipoles\n"
                "(4) + Quadrupoles\n"
                "(5) + Octupoles\n"
                "(6) + Hexadecapoles\n\n"
                "Enter option number: "
            ).strip()

            if choice in choice_map:
                break
            else:
                print("Invalid input. Please enter a number between 1 and 6.")

        level = choice_map[choice]
        props = AVAILABLE_PROPS[level]

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

        print(remaining_geometries_message("training"))

        training_sets = []

        while True:
            current = ", ".join(map(str, training_sets)) if training_sets else "none"

            user_input = input(
                f"Currently selected: {current}\n"
                "Enter training set size (type 'q' to finish): "
            )

            if user_input in ("q", "quit"):
                if not training_sets:
                    print("You must enter at least one training size.")
                    continue
                break

            try:
                value = int(user_input)

                if value <= 0:
                    print("Please enter a positive integer.")
                    continue

                training_sets.append(value)

            except ValueError:
                print("Invalid input. Please enter an integer or 'done' to finish.")

        submit_data_prep_menu_options.selected_train_size = training_sets

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Training set size(s) {submit_data_prep_menu_options.selected_train_size}"
        )

    @staticmethod
    def select_val_size():
        """Asks user to select the size of the validation set for testing."""
        print(remaining_geometries_message("validation"))

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
        print(remaining_geometries_message("test"))

        submit_data_prep_menu_options.selected_test_size = user_input_int(
            "Enter test set size: ",
            submit_data_prep_menu_options.selected_test_size,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Test set size {submit_data_prep_menu_options.selected_test_size}"
        )

    @staticmethod
    def submit_data_prep_on_compute():
        """Submits polus job for data preparation."""
        ncores, props, q00_threshold, train_size, val_size, test_size = (
            submit_data_prep_menu_options.selected_number_of_cores,
            submit_data_prep_menu_options.selected_props,
            submit_data_prep_menu_options.selected_q00_threshold,
            submit_data_prep_menu_options.selected_train_size,
            submit_data_prep_menu_options.selected_val_size,
            submit_data_prep_menu_options.selected_test_size,
        )

        input_path = Path(ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH)
        has_csv = any(input_path.glob("*.csv"))

        if not has_csv:
            print_summary_and_pause(
                "DATASET SPLITTING JOB NOT SUBMITTED",
                {"Input directory": input_path},
                [
                    "No csv files were found in the directory selected, so there is "
                    "nothing to split into training, validation and test sets.",
                    "The input directory is the folder of per-atom csv files made by "
                    "'Make csvs from database' in the points directory menu (usually a "
                    "*_processed_csvs folder), not the database or PointsDirectory "
                    "itself.",
                ],
            )
            return

        script_path, system_dir = write_dataset_prep(
            outlier_input_dir=input_path,
            q00_threshold=q00_threshold,
            props=props,
            train_size=train_size,
            val_size=val_size,
            test_size=test_size,
        )

        job_id = submit_polus(
            input_script=script_path,
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES["datasets"],
            cwd=system_dir,
            ncores=ncores,
        )

        train_sizes = (
            ", ".join(str(size) for size in train_size)
            if isinstance(train_size, (list, tuple))
            else str(train_size)
        )

        print_summary_and_pause(
            "DATASET SPLITTING JOB SUBMITTED",
            {
                "Input csv directory": input_path,
                "Dataset directory": system_dir,
                "Job ID": job_id.id if job_id else "not available",
                "Properties": ", ".join(props),
                "Training set size(s)": train_sizes,
                "Validation set size": val_size,
                "Test set size": test_size,
                "q00 outlier threshold": q00_threshold,
                "CPU cores": ncores,
            },
            [
                "The job filters out points whose q00 is further than the threshold "
                "from the mean, then splits what is left into training, validation and "
                "test sets, one set of files per atom and property.",
                "Giving several training set sizes builds a separate training folder "
                "for each of them, which is what a learning curve is made from.",
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue), then point the "
                "model training menu at the dataset directory above.",
            ],
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
