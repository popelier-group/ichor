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

SUBMIT_GAUSSIAN_MENU_DESCRIPTION = MenuDescription(
    "Submit GAUSSIAN Menu",
    subtitle="Use this menu to optimise a geometry with GAUSSIAN.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_GAUSSIAN_MENU_DEFAULTS = {
    "default_method": "b3lyp",
    "default_ncores": 2,
    "default_naat": 1,
    "default_encomp": 3,
}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitGAUSSIANMenuOptions(MenuOptions):

    selected_method: str
    selected_number_of_cores: str
    selected_naat: int
    selected_encomp: bool


# initialize dataclass for storing information for menu
submit_gaussian_menu_options = SubmitGAUSSIANMenuOptions(
    *SUBMIT_GAUSSIAN_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitGAUSSIANFunctions:
    @staticmethod
    def select_method():
        """Asks user to update the ethod for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_gaussian_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_gaussian_menu_options.selected_method
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to select number of cores."""
        submit_gaussian_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_gaussian_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_naat():
        """Asks user to select AIMAll -naat setting"""
        submit_gaussian_menu_options.selected_naat = user_input_int(
            "Select 'naat' setting: ",
            submit_gaussian_menu_options.selected_naat,
        )

    @staticmethod
    def select_encomp():
        """Asks user to select AIMAll -encomp setting"""

        submit_gaussian_menu_options.selected_encomp = user_input_int(
            "Select 'encomp' setting: ",
            submit_gaussian_menu_options.selected_encomp,
        )

    @staticmethod
    def points_directory_to_aimall_on_compute():
        """Submits a single PointsDirectory or many PointsDirectory-ies to AIMAll on compute."""

        method, ncores, naat, encomp = (
            submit_gaussian_menu_options.selected_method,
            submit_gaussian_menu_options.selected_number_of_cores,
            submit_gaussian_menu_options.selected_naat,
            submit_gaussian_menu_options.selected_encomp,
        )

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
                submit_points_directory_to_aimall(
                    points_directory=pd,
                    method=method,
                    ncores=ncores,
                    naat=naat,
                    encomp=encomp,
                    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE[
                        "outputs"
                    ]
                    / pd.path.name
                    / "AIMALL",
                    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                    / pd.path.name
                    / "AIMALL",
                )

        else:
            pd = PointsDirectory(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )

            submit_points_directory_to_aimall(
                points_directory=pd,
                method=method,
                ncores=ncores,
                naat=naat,
                encomp=encomp,
                outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
                / pd.path.name
                / "AIMALL",
                errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                / pd.path.name
                / "AIMALL",
            )


# make menu items
# can use lambda functions to change text of options as well :)
submit_gaussian_menu_items = [
    FunctionItem(
        "Change method",
        SubmitGAUSSIANFunctions.select_method,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitGAUSSIANFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change 'naat' setting",
        SubmitGAUSSIANFunctions.select_naat,
    ),
    FunctionItem(
        "Change 'encomp' setting",
        SubmitGAUSSIANFunctions.select_encomp,
    ),
    FunctionItem(
        "Submit AIMAll to compute nodes",
        SubmitGAUSSIANFunctions.points_directory_to_aimall_on_compute,
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
