import os
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    directory_selected,
    maximum_cores,
    print_summary_and_pause,
    user_input_float,
    user_input_int,
    user_input_path,
    user_input_restricted,
)

from ichor.hpc.main import (
    find_and_setup_ferebus_subdirs,
    pyferebus_platform,
    write_extract_models_script,
    write_pyferebus_input_script,
)


# override path display to menu
def display_path(p: Path, keep=3):
    parts = p.parts
    if len(parts) <= keep:
        return str(p)
    return "..." + str(Path(*parts[-keep:]))


AVAILABLE_MEAN_TYPES = {
    "physical": 15,
}

AVAILABLE_KERNEL_TYPES = {
    "rbfc_per": "rbfc_per",
}

# how the training sets are selected, so that an option which needs them but has not
# been given any says what to do about it
SELECT_INPUT_WITH = (
    "Use 'Select input data folder' in this menu to select the dataset directory made "
    "by the Dataset Preparation Menu (either one dataset folder or the parent holding "
    "several of them); the training folders under it are found when it is selected."
)

SUBMIT_TRAINING_MENU_DESCRIPTION = MenuDescription(
    "Model Training Menu",
    subtitle="Use this menu to train your GPR models.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_TRAINING_MENU_DEFAULTS = {
    "default_input": "",
    "default_training_folders": [],
    "default_ncores": 20,
    "default_kernel": "rbfc_per",
    "default_max_iter": 100,
    "default_huber_delta": 0.05,
    "default_mean_type": "physical",
    "default_gwo_cycles": 1,
}


# dataclass used to store values for SubmitTrainingLMenu
@dataclass
class SubmitTrainingMenuOptions(MenuOptions):
    selected_input_directory_path: Path
    selected_train_folders: list[Path]
    selected_number_of_cores: int
    selected_kernel: str
    selected_max_iter: int
    selected_huber_delta: float
    selected_mean_type: str
    selected_gwo_cycles: int

    def check_machine_is_known(self) -> Optional[str]:
        """Checks that the machine ichor is running on is in the ichor config, as it
        is the platform the pyferebus jobs are set up for. Without it pyferebus
        falls back to its own default platform, which is likely to be the wrong
        batch system."""
        if not pyferebus_platform():
            return (
                "The machine ichor is running on is not in the ichor config, so "
                "the training jobs cannot be told which platform to be set up "
                "for and pyferebus falls back to its own default."
            )

    def check_selected_number_of_cores(self) -> Optional[str]:
        """Checks that each training job asks for at least one core."""
        ncores = self.selected_number_of_cores
        if not isinstance(ncores, int) or ncores < 1:
            return f"Current number of cores: {ncores} must be 1 or greater."

    def check_number_of_cores_fits_machine(self) -> Optional[str]:
        """Checks that a training job does not ask for more cores than the machine can
        give it. One job is submitted per training folder, so a number the batch system
        refuses is a number every one of them is refused for."""
        ncores = self.selected_number_of_cores
        if not isinstance(ncores, int):
            return None

        largest = maximum_cores()
        if largest and ncores > largest:
            return (
                f"Current number of cores: {ncores:,} is more than the {largest:,} a "
                "job can ask for on this machine, so every training job would be "
                "refused by the batch system."
            )

    def get_display_value(self, value, keep_first=1):

        # Single path -> shorten normally
        if isinstance(value, Path):
            return display_path(value)

        # List of paths (the training sets found under the input directory) -> lead with
        # how many there are, as the list itself is truncated to keep the menu on one
        # screen and the number of sets loaded cannot be counted off a truncated list
        if isinstance(value, list) and (not value or isinstance(value[0], Path)):
            n = len(value)

            if n == 0:
                return "0 (select an input data folder)"

            # Shorten each path
            short = [display_path(p) for p in value]

            # Long lists -> first `keep_first`, ellipsis, last 1
            if n > keep_first + 1:
                short = short[:keep_first] + ["..."] + [short[-1]]

            return f"{n} loaded ({', '.join(short)})"

        return value


# initialize dataclass for storing information for menu
submit_training_menu_options = SubmitTrainingMenuOptions(
    *SUBMIT_TRAINING_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitTrainingFunctions:
    @staticmethod
    def select_input_directory():
        """Asks user to update path to directory containing training folders, then
        searches it for the training sets to train on. The search walks the whole tree
        under the given directory, which takes a while on a shared filesystem, so it is
        shown with a progress bar and what it found is summarised afterwards (the menu
        is redrawn over the output of the search otherwise)."""
        pd_path = user_input_path("Change Directory Path: ")
        ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_training_menu_options.selected_input_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH
        )
        input_directory = submit_training_menu_options.selected_input_directory_path

        if not input_directory.is_dir():
            submit_training_menu_options.selected_train_folders = []
            print_summary_and_pause(
                "NO TRAINING SETS LOADED",
                {"Input directory": input_directory},
                [
                    "That path is not a directory, so there was nothing to search for "
                    "training sets.",
                    SELECT_INPUT_WITH,
                ],
            )
            return

        print(f"\nSearching {input_directory} for training sets...\n")

        training_dirs = find_and_setup_ferebus_subdirs(input_directory)
        submit_training_menu_options.selected_train_folders = training_dirs

        if not training_dirs:
            print_summary_and_pause(
                "NO TRAINING SETS LOADED",
                {"Input directory": input_directory},
                [
                    "No TRAIN folders holding a job-details file were found under that "
                    "directory, so there is nothing to train on.",
                    SELECT_INPUT_WITH,
                ],
            )
            return

        print_summary_and_pause(
            "TRAINING SETS LOADED",
            {
                "Input directory": input_directory,
                "Training sets loaded": len(training_dirs),
            },
            [
                "One training job is submitted per training set loaded when 'Submit "
                "for training' is picked, each training a GPR model for every atom and "
                "property of that training set size.",
            ],
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to select the number of cores each training job asks for.

        One job is submitted per training folder and each asks for this many cores, so
        the most a job can ask for on this machine is printed above the prompt: a job
        asking for more than that is refused by the batch system rather than queued."""

        # one short line, as this is printed just above the prompt
        largest = maximum_cores()
        if largest:
            print(f"\nA job can ask for up to {largest:,} cores on this machine.\n")

        submit_training_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_training_menu_options.selected_number_of_cores,
            minimum=1,
        )

    @staticmethod
    def select_kernel():
        """Asks user to select kernel."""
        submit_training_menu_options.selected_kernel = user_input_restricted(
            AVAILABLE_KERNEL_TYPES.keys(),
            "Enter kernel type: ",
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
        )

    @staticmethod
    def select_gwo_cycles():
        """Asks user to select gwo cycles."""
        submit_training_menu_options.selected_gwo_cycles = user_input_int(
            "Enter gwo cycles: ",
            submit_training_menu_options.selected_gwo_cycles,
        )

    @staticmethod
    def submit_training_on_compute():

        # the input directory defaults to the directory ichor is running in, in which
        # nothing would be found to train on
        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_DIRECTORY_PATH,
            "submit the model training",
            what="dataset directory",
            select_with=SELECT_INPUT_WITH,
        ):
            return

        train_folders = submit_training_menu_options.selected_train_folders

        if not train_folders:
            print_summary_and_pause(
                "MODEL TRAINING NOT SUBMITTED",
                {
                    "Input directory": (
                        submit_training_menu_options.selected_input_directory_path
                    )
                },
                [
                    "No TRAIN folders holding a job-details file were found under the "
                    "selected directory, so there is nothing to train.",
                    SELECT_INPUT_WITH,
                    "Those folders are the ones made by the Dataset Preparation Menu, "
                    "each holding the training, validation and test files of one "
                    "training set size.",
                ],
            )
            return

        # the directory ichor is running in, so that it can be restored afterwards
        original_working_directory = Path.cwd()

        submitted_folders = []
        failed_folders = []

        # os.chdir below leaves ichor in the last training folder otherwise, which makes
        # every later menu write its output somewhere unexpected. It has to be restored
        # even when a submission raises, hence the try/finally.
        try:
            for job_details_path in train_folders:
                workdir = job_details_path.parent  # SEQ-XX-25-25 folder
                print(f"\n=== Running pyferebus in {workdir} ===")
                # Change into the working directory
                os.chdir(workdir)

                """Creates and submits models for training."""
                # key:values from dictionaries
                kernel_type_key = submit_training_menu_options.selected_kernel
                mean_type_key = submit_training_menu_options.selected_mean_type

                ncores, kernel, max_iter, huber_delta, mean_type, gwo_cycles = (
                    submit_training_menu_options.selected_number_of_cores,
                    AVAILABLE_KERNEL_TYPES[kernel_type_key],
                    submit_training_menu_options.selected_max_iter,
                    submit_training_menu_options.selected_huber_delta,
                    AVAILABLE_MEAN_TYPES[mean_type_key],
                    submit_training_menu_options.selected_gwo_cycles,
                )

                pyferebus_input_script = write_pyferebus_input_script(
                    input_dir=workdir,
                    ncores=ncores,
                    kernel=kernel,
                    max_iter=max_iter,
                    huber_delta=huber_delta,
                    mean_type=mean_type,
                    gwo_cycles=gwo_cycles,
                )

                write_extract_models_script()

                # run the pyferebus input script. As submit on compute is hard coded to
                # true pyferebus will handle the submission

                try:
                    subprocess.run(
                        ["python3", pyferebus_input_script.name],
                        cwd=workdir,
                        check=True,
                    )
                # one training set failing to submit (an error from pyferebus, or no
                # python3 on the machine) used to take the whole menu down with it,
                # losing every setting made in it. The rest are still tried and what
                # failed is reported at the end instead.
                except (subprocess.CalledProcessError, OSError) as error:
                    failed_folders.append(workdir)
                    print(f"\nCould not submit {workdir}: {error}")
                    ichor.hpc.global_variables.LOGGER.error(
                        f"Training job for {workdir} was not submitted: {error}"
                    )
                else:
                    submitted_folders.append(workdir)
        finally:
            os.chdir(original_working_directory)

        if not submitted_folders:
            print_summary_and_pause(
                "MODEL TRAINING NOT SUBMITTED",
                {
                    "Input directory": (
                        submit_training_menu_options.selected_input_directory_path
                    ),
                    "Training folders tried": len(train_folders),
                },
                [
                    "None of the training folders could be submitted. The error given "
                    "for each of them is printed above this summary, and is in the "
                    "ichor log as well.",
                    "The settings in this menu are written into the pyferebus_input.py "
                    "of every training folder, so that script can be run by hand in one "
                    "of them to see the same error.",
                ],
            )
            return

        print_summary_and_pause(
            "MODEL TRAINING JOBS SUBMITTED",
            {
                "Input directory": (
                    submit_training_menu_options.selected_input_directory_path
                ),
                "Training folders": (
                    f"{len(submitted_folders)} of {len(train_folders)} "
                    "(one job per folder)"
                ),
                "Platform": pyferebus_platform() or "pyferebus default",
                "Kernel": submit_training_menu_options.selected_kernel,
                "Mean type": submit_training_menu_options.selected_mean_type,
                "Max iterations": submit_training_menu_options.selected_max_iter,
                "Huber delta": submit_training_menu_options.selected_huber_delta,
                "GWO cycles": submit_training_menu_options.selected_gwo_cycles,
                "CPU cores per job": (
                    submit_training_menu_options.selected_number_of_cores
                ),
            },
            [
                *(
                    [
                        f"{len(failed_folders)} of the {len(train_folders)} training "
                        "folders could not be submitted. The error given for each of "
                        "them is printed above this summary, and is in the ichor log "
                        "as well."
                    ]
                    if failed_folders
                    else []
                ),
                "One pyferebus job has been submitted per training folder above, "
                "each training a GPR model for every atom and property of that "
                "training set size.",
                "The jobs are now queued on compute nodes, so they will not start "
                "immediately and this menu does not wait for them. Check on them with "
                "your batch system's queue command (e.g. qstat / squeue).",
                "The trained .model files are written into the training folders "
                "themselves. Once they are there, the model analysis menu makes "
                "S-curves and quality metrics from them.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info("Training models job submitted")


# make menu items
# can use lambda functions to change text of options as well :)
submit_training_menu_items = [
    FunctionItem(
        "Select input data folder",
        SubmitTrainingFunctions.select_input_directory,
    ),
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
