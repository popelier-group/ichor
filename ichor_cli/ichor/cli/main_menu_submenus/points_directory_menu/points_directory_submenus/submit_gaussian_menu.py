from dataclasses import dataclass

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_bool,
    user_input_free_flow,
    user_input_int,
)
from ichor.core.files import PointsDirectory
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main import submit_points_directory_to_gaussian
from ichor.hpc.submission_commands import GaussianCommand

SUBMIT_GAUSSIAN_MENU_DESCRIPTION = MenuDescription(
    "Submit Gaussian Menu",
    subtitle="Use this menu to submit a PointsDirectory to Gaussian.\n",
)

SUBMIT_GAUSSIAN_MENU_DEFAULTS = {
    "default_method": "b3lyp",
    "default_basis_set": "6-31+g(d,p)",
    "default_ncores": 2,
    "default_overwrite_existing_gjfs": False,
    "default_force_calculate_wfn": False,
}


# dataclass used to store values for SubmitGaussianMenu
@dataclass
class SubmitGaussianMenuOptions(MenuOptions):

    selected_method: str
    selected_basis_set: str
    selected_number_of_cores: int
    selected_overwrite_existing_gjfs: bool
    selected_force_calculate_wfn: bool


# initialize dataclass for storing information for menu
submit_gaussian_menu_options = SubmitGaussianMenuOptions(
    *SUBMIT_GAUSSIAN_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitGaussianFunctions:
    @staticmethod
    def select_method():
        """Asks user to update the method for Gaussian"""
        submit_gaussian_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_gaussian_menu_options.selected_method
        )

    @staticmethod
    def select_basis_set():
        """Asks user to update the basis set."""
        submit_gaussian_menu_options.selected_basis_set = user_input_free_flow(
            "Enter basis set: ", submit_gaussian_menu_options.selected_basis_set
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to update the basis set."""
        submit_gaussian_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_gaussian_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_overwrite_existing_gjfs():
        """Asks user whether or not to overwrite existing gjfs"""
        submit_gaussian_menu_options.selected_overwrite_existing_gjfs = user_input_bool(
            "Overwrite existing gjfs (yes/no): ",
            submit_gaussian_menu_options.selected_overwrite_existing_gjfs,
        )

    @staticmethod
    def select_force_calculate_wfns():
        """Whether or not to recalculate wfns if they are already present"""

        submit_gaussian_menu_options.selected_force_calculate_wfn = user_input_bool(
            "Recalculate present wfns (yes/no): ",
            submit_gaussian_menu_options.selected_force_calculate_wfn,
        )

    @staticmethod
    def points_directory_to_gaussian_on_compute():
        """Submits a single PointsDirectory to Gaussian on compute."""

        (method, basis_set, ncores, overwrite_existing, force_calculate_wfn) = (
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_basis_set,
            submit_gaussian_menu_options.selected_number_of_cores,
            submit_gaussian_menu_options.selected_overwrite_existing_gjfs,
            submit_gaussian_menu_options.selected_force_calculate_wfn,
        )

        # add memory link0 to GJF
        mem_per_core = GaussianCommand.memory_per_core
        mem = (mem_per_core - 1) * ncores
        link0 = [f"NProcShared={ncores}", f"Mem={mem}"]

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )
        )

        # if containing many PointsDirectory
        if is_parent_directory_to_many_points_directories:

            for (
                d
            ) in (
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.iterdir()
            ):

                pd = PointsDirectory(d)

                submit_points_directory_to_gaussian(
                    points_directory=pd,
                    overwrite_existing=overwrite_existing,
                    force_calculate_wfn=force_calculate_wfn,
                    ncores=ncores,
                    method=method,
                    basis_set=basis_set,
                    link0=link0,
                    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE[
                        "outputs"
                    ]
                    / pd.path.name
                    / "GAUSSIAN",
                    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                    / pd.path.name
                    / "GAUSSIAN",
                )

        # if containing one PointsDirectory
        else:
            pd = PointsDirectory(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )

            submit_points_directory_to_gaussian(
                points_directory=pd,
                overwrite_existing=overwrite_existing,
                force_calculate_wfn=force_calculate_wfn,
                ncores=ncores,
                method=method,
                basis_set=basis_set,
                link0=link0,
                outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
                / pd.path.name
                / "GAUSSIAN",
                errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                / pd.path.name
                / "GAUSSIAN",
            )


# make menu items
# can use lambda functions to change text of options as well :)
submit_gaussian_menu_items = [
    FunctionItem(
        "Change method",
        SubmitGaussianFunctions.select_method,
    ),
    FunctionItem(
        "Change basis set",
        SubmitGaussianFunctions.select_basis_set,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitGaussianFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Overwrite GJF files (if any are already present)",
        SubmitGaussianFunctions.select_overwrite_existing_gjfs,
    ),
    FunctionItem(
        "Recalculate all WFNs (if any are already present)",
        SubmitGaussianFunctions.select_force_calculate_wfns,
    ),
    FunctionItem(
        "Submit to Gaussian",
        SubmitGaussianFunctions.points_directory_to_gaussian_on_compute,
    ),
]

# initialize menu
submit_gaussian_menu = ConsoleMenu(
    this_menu_options=submit_gaussian_menu_options,
    title=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_GAUSSIAN_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_gaussian_menu, submit_gaussian_menu_items)
