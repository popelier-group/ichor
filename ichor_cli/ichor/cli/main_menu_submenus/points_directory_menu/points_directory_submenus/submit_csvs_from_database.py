import math
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    user_input_bool,
    user_input_int,
    user_input_path,
    user_input_restricted,
)

from ichor.core.database.query_database import (
    get_alf_from_first_db_geometry,
    write_processed_data_for_atoms_parallel,
)

from ichor.hpc.main import submit_make_csvs_from_database
from ichor.hpc.main.database import AVAILABLE_DATABASE_FORMATS

SUBMIT_CSVS_MENU_DESCRIPTION = MenuDescription(
    "Database Processing Menu",
    subtitle="Use this menu to get things from a database.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_CSVS_MENU_DEFAULTS = {
    "default_database_format": "sqlite",
    "default_rotate_multipole_moments": True,
    "default_calculate_feature_forces": False,
    "default_number_of_cores": 4,
    "default_submit_on_compute": True,
}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitCSVSMenuOptions(MenuOptions):

    selected_database_path: Path
    selected_database_format: str
    selected_rotate_multipole_moments: bool
    selected_calculate_feature_forces: bool
    selected_number_of_cores: int
    selected_submit_on_compute: bool

    def check_selected_database_path(self) -> Union[str, None]:
        """Checks whether the given database exists or if it is a file."""
        db_path = Path(self.selected_database_path)
        if not db_path.exists():
            return f"Current database path: {db_path} does not exist."
        elif not db_path.is_file():
            return f"Current file path: {db_path} is not a file."


# initialize dataclass for storing information for menu
submit_csvs_menu_options = SubmitCSVSMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH,
    *SUBMIT_CSVS_MENU_DEFAULTS.values(),
)


# class with static methods for each menu item that calls a function.
class SubmitCSVSFunctions:
    @staticmethod
    def select_database_path():
        """
        Asks user to select path to database
        """
        db_path = user_input_path("Change database path: ")
        ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH = Path(
            db_path
        ).absolute()
        submit_csvs_menu_options.selected_database_path = (
            ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH
        )

    @staticmethod
    def select_database_format():
        """Asks user to update the ethod for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_csvs_menu_options.selected_database_format = user_input_restricted(
            AVAILABLE_DATABASE_FORMATS.keys(),
            "Choose a database format: ",
            submit_csvs_menu_options.selected_database_format,
        )

    @staticmethod
    def select_rotate_multipole_moments():
        """
        Asks user whether or not to rotate multipole moments.
        """

        submit_csvs_menu_options.selected_rotate_multipole_moments = user_input_bool(
            "Calculate rotated multipole moments (yes/no): ",
            submit_csvs_menu_options.selected_rotate_multipole_moments,
        )

    @staticmethod
    def select_calculate_feature_forces():
        """
        Asks user whether to calculate forces in ALF coordinates.
        """

        submit_csvs_menu_options.selected_calculate_feature_forces = user_input_bool(
            "Calculate feature forces (yes/no): ",
            submit_csvs_menu_options.selected_calculate_feature_forces,
        )

    @staticmethod
    def select_number_of_cores():
        """
        Asks user for the number of cores.
        """

        submit_csvs_menu_options.selected_number_of_cores = user_input_int(
            "Number of cores: ", submit_csvs_menu_options.selected_number_of_cores
        )

    @staticmethod
    def select_submit_on_compute():
        """
        Asks user whether or not to submit database making on compute.
        """

        submit_csvs_menu_options.selected_submit_on_compute = user_input_bool(
            "Submit on compute (yes/no): ",
            submit_csvs_menu_options.selected_submit_on_compute,
        )

    @staticmethod
    def make_csvs_from_database():
        """Makes csv files containing features, iqa energies, and rotated multipole moments given a database"""

        db_path = ichor.cli.global_menu_variables.SELECTED_DATABASE_PATH
        db_type = submit_csvs_menu_options.selected_database_format

        rotate_multipole_moments = (
            submit_csvs_menu_options.selected_rotate_multipole_moments
        )
        calculate_feature_forces = (
            submit_csvs_menu_options.selected_calculate_feature_forces
        )
        ncores = submit_csvs_menu_options.selected_number_of_cores
        submit_on_compute = submit_csvs_menu_options.selected_submit_on_compute

        # make into a very large number to export full database to polus
        float_integration_error = 100000000.0
        float_difference_iqa_wfn = 10000000.0

        if not submit_on_compute:
            alf = get_alf_from_first_db_geometry(db_path, db_type)
            write_processed_data_for_atoms_parallel(
                db_path,
                db_type,
                alf,
                ncores,
                max_diff_iqa_wfn=float_difference_iqa_wfn,
                max_integration_error=float_integration_error,
                calc_multipoles=rotate_multipole_moments,
                calc_forces=calculate_feature_forces,
            )

        # if running on compute
        else:

            submit_make_csvs_from_database(
                db_path,
                db_type,
                ncores=ncores,
                alf=None,
                float_difference_iqa_wfn=float_difference_iqa_wfn,
                float_integration_error=float_integration_error,
                rotate_multipole_moments=rotate_multipole_moments,
                calculate_feature_forces=calculate_feature_forces,
            )


# make menu items
# can use lambda functions to change text of options as well :)
submit_csvs_menu_items = [
    FunctionItem(
        "Change database path",
        SubmitCSVSFunctions.select_database_path,
    ),
    FunctionItem(
        "Change database format",
        SubmitCSVSFunctions.select_database_format,
    ),
    FunctionItem(
        "Change rotate multipole moments",
        SubmitCSVSFunctions.select_rotate_multipole_moments,
    ),
    FunctionItem(
        "Change calculate feature forces",
        SubmitCSVSFunctions.select_calculate_feature_forces,
    ),
    FunctionItem(
        "Change number of cores, parallelized over number of atoms",
        SubmitCSVSFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change submit to compute", SubmitCSVSFunctions.select_submit_on_compute
    ),
    FunctionItem(
        "Make csvs from database", SubmitCSVSFunctions.make_csvs_from_database
    ),
]

# initialize menu
submit_csvs_menu = ConsoleMenu(
    this_menu_options=submit_csvs_menu_options,
    title=SUBMIT_CSVS_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_CSVS_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_CSVS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_CSVS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_CSVS_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_csvs_menu, submit_csvs_menu_items)
