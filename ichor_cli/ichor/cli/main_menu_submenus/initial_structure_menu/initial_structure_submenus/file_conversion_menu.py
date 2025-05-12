from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.initial_structure_menu import (
    AVAILABLE_WRITE_FILE_FORMATS,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import user_input_path, user_input_restricted
from ichor.core.files import PointsDirectory
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main import submit_points_directory_to_aimall

FILE_CONVERSION_MENU_DESCRIPTION = MenuDescription(
    "File Conversion Menu",
    subtitle="Use this menu to to convert between common file types.\n",
)

FILE_CONVERSION_MENU_DEFAULTS = {
    "default_output_file": ".xyz",
}

# dataclass used to store values for FileConversionMenu


@dataclass
class FileConversionMenuOptions(MenuOptions):
    selected_input_file_path: Path
    selected_output_file_format: str

    def check_selected_file_path(self) -> Union[str, None]:
        """Checks whether the given file exists."""
        db_path = Path(self.selected_input_file_path)
        if not db_path.exists():
            return f"Current file path: {db_path} does not exist."


# initialize dataclass for storing information for menu
file_conversion_menu_options = FileConversionMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH,
    *FILE_CONVERSION_MENU_DEFAULTS.values(),
)


# class with static methods for each menu item that calls a function.
class FileConversionFunctions:
    @staticmethod
    def select_input_file_path():
        """Asks user to select path to input file"""

        db_path = user_input_path("Change database path: ")
        ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH = Path(
            db_path
        ).absolute()
        file_conversion_menu_options.selected_input_file_path = (
            ichor.cli.global_menu_variables.SELECTED_INPUT_FILE_PATH
        )

    @staticmethod
    def select_output_file_format():
        """Asks user to select the output file format eg .mol, .xyz."""

        file_conversion_menu_options.selected_output_file_format = (
            user_input_restricted(
                AVAILABLE_WRITE_FILE_FORMATS.keys(),
                "Choose an output file format: ",
                file_conversion_menu_options.selected_output_file_format,
            )
        )

    @staticmethod
    def points_directory_to_aimall_on_compute():
        """Submits a single PointsDirectory or many PointsDirectory-ies to AIMAll on compute."""

        method, ncores, naat, encomp = (
            file_conversion_menu_options.selected_method,
            file_conversion_menu_options.selected_number_of_cores,
            file_conversion_menu_options.selected_naat,
            file_conversion_menu_options.selected_encomp,
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
file_conversion_menu_items = [
    FunctionItem(
        "Change input file path",
        FileConversionFunctions.select_input_file_path,
    ),
    FunctionItem(
        "Change output file format",
        FileConversionFunctions.select_output_file_format,
    ),
    FunctionItem(
        "Convert file format",
        FileConversionFunctions.points_directory_to_aimall_on_compute,
    ),
]

# initialize menu
file_conversion_menu = ConsoleMenu(
    this_menu_options=file_conversion_menu_options,
    title=FILE_CONVERSION_MENU_DESCRIPTION.title,
    subtitle=FILE_CONVERSION_MENU_DESCRIPTION.subtitle,
    prologue_text=FILE_CONVERSION_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=FILE_CONVERSION_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=FILE_CONVERSION_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(file_conversion_menu, file_conversion_menu_items)
