from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

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
from ichor.core.files import PointsDirectory, PointsDirectoryParent
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main import submit_points_directory_to_aimall

SUBMIT_AIMALL_MENU_DESCRIPTION = MenuDescription(
    "Submit AIMAll Menu",
    subtitle="Use this menu to submit a PointsDirectory to AIMAll.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_AIMALL_MENU_DEFAULTS = {
    "default_method": "b3lyp",
    "default_ncores": 2,
    "default_naat": 1,
    "default_encomp": 3,
}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitAIMALLMenuOptions(MenuOptions):

    selected_method: str
    selected_number_of_cores: str
    selected_naat: int
    selected_encomp: bool

    # defaults to the current working directory
    selected_points_directory_path: Path = field(default_factory=lambda: Path.cwd())

    def check_path(self):

        pd_path = Path(self.selected_points_directory_path)
        if not pd_path.is_dir():
            return "Current path is not a directory."

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (pd_path.suffix != PointsDirectory._suffix) and (
            pd_path.suffix != PointsDirectoryParent._suffix
        ):
            return f"Current path: {pd_path} might not be PointsDirectory-like)."


# initialize dataclass for storing information for menu
submit_aimall_menu_options = SubmitAIMALLMenuOptions(
    *SUBMIT_AIMALL_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitAIMALLFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_aimall_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def select_method():
        """Asks user to update the method for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_aimall_menu_options.selected_method = user_input_free_flow(
            "Enter method: ", submit_aimall_menu_options.selected_method
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to select number of cores."""
        submit_aimall_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_aimall_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_naat():
        """Asks user to select AIMAll -naat setting"""
        submit_aimall_menu_options.selected_naat = user_input_int(
            "Select 'naat' setting: ",
            submit_aimall_menu_options.selected_naat,
        )

    @staticmethod
    def select_encomp():
        """Asks user to select AIMAll -encomp setting"""

        submit_aimall_menu_options.selected_encomp = user_input_int(
            "Select 'encomp' setting: ",
            submit_aimall_menu_options.selected_encomp,
        )

    @staticmethod
    def points_directory_to_aimall_on_compute():
        """Submits a single PointsDirectory or many PointsDirectory-ies to AIMAll on compute."""

        method, ncores, naat, encomp = (
            submit_aimall_menu_options.selected_method,
            submit_aimall_menu_options.selected_number_of_cores,
            submit_aimall_menu_options.selected_naat,
            submit_aimall_menu_options.selected_encomp,
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
        answer = ""
        user_input_free_flow(
            "AIMALL COMPUTATION SUBMITTED. Press enter to continue: ", answer
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_aimall_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        SubmitAIMALLFunctions.select_points_directory,
    ),
    FunctionItem(
        "Change method",
        SubmitAIMALLFunctions.select_method,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitAIMALLFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change 'naat' setting",
        SubmitAIMALLFunctions.select_naat,
    ),
    FunctionItem(
        "Change 'encomp' setting",
        SubmitAIMALLFunctions.select_encomp,
    ),
    FunctionItem(
        "Submit AIMAll to compute nodes",
        SubmitAIMALLFunctions.points_directory_to_aimall_on_compute,
    ),
]

# initialize menu
submit_aimall_menu = ConsoleMenu(
    this_menu_options=submit_aimall_menu_options,
    title=SUBMIT_AIMALL_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_AIMALL_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_AIMALL_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_AIMALL_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_AIMALL_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_aimall_menu, submit_aimall_menu_items)
