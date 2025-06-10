from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_free_flow,
    user_input_int,
    user_input_path,
)
from ichor.core.files import PointsDirectory
from ichor.hpc.main import submit_single_gaussian_xyz

SUBMIT_GAUSSIAN_MENU_DESCRIPTION = MenuDescription(
    "Submit Gaussian Menu",
    subtitle="Use this menu to optimise a single geometry with Gaussian.\n",
)

SUBMIT_GAUSSIAN_MENU_DEFAULTS = {
    "default_keywords": "opt",
    "default_method": "b3lyp",
    "default_basis_set": "6-31+g(d,p)",
    "default_ncores": 2,
    "default_gjf": "",
}


# dataclass used to store values for SubmitGaussianMenu
@dataclass
class SubmitGaussianMenuOptions(MenuOptions):
    selected_keywords: str
    selected_method: str
    selected_basis_set: str
    selected_number_of_cores: int
    selected_gjf_path: str


# initialize dataclass for storing information for menu
submit_gaussian_menu_options = SubmitGaussianMenuOptions(
    *SUBMIT_GAUSSIAN_MENU_DEFAULTS.values()
)

# set keywords to opt as default
submit_gaussian_menu_options.selected_keywords = "opt"


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
    def xyz_to_gaussian_on_compute():
        """Converts a single xyz to gjf and submit to Gaussian on compute."""
        (
            keywords,
            method,
            basis_set,
            ncores,
        ) = (
            submit_gaussian_menu_options.selected_keywords,
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_basis_set,
            submit_gaussian_menu_options.selected_number_of_cores,
        )

        if len(ichor.cli.global_menu_variables.SELECTED_GJF_PATH):
            print("ALTERNATIVE FUNCTION FOR BUILDING NEW GJF FROM AN XYZ")
            xyz_geom_for_opt = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
            submit_single_gaussian_xyz(
                input_file_path=xyz_geom_for_opt,
                ncores=ncores,
                keywords=keywords,
                method=method,
                basis_set=basis_set,
                outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
                / xyz_geom_for_opt.path.name
                / "GAUSSIAN",
                errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                / xyz_geom_for_opt.path.name
                / "GAUSSIAN",
            )
        else:
            print("SOME FUNCTION FOR SUBMITTING GJF FILE AS IS")

    @staticmethod
    def select_existing_gjf():
        """Asks user to input existing gjf file as input."""
        gjf_path = user_input_path("Enter .gjf path to submit existing Gaussian job: ")
        ichor.cli.global_menu_variables.SELECTED_GJF_PATH = Path(gjf_path).absolute()
        submit_gaussian_menu_options.selected_gjf_path = (
            ichor.cli.global_menu_variables.SELECTED_GJF_PATH
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
        "Submit to Gaussian",
        SubmitGaussianFunctions.xyz_to_gaussian_on_compute,
    ),
    FunctionItem(
        "Select exisiting .gjf file",
        SubmitGaussianFunctions.select_existing_gjf,
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
