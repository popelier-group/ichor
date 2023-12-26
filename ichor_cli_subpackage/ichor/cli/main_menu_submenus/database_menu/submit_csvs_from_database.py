import math
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
    user_input_bool,
    user_input_float,
    user_input_int,
    user_input_path,
)

from ichor.core.sql.query_database import (
    get_alf_from_first_db_geometry,
    write_processed_data_for_atoms_parallel,
)

from ichor.hpc.main import submit_make_csvs_from_database

SUBMIT_CSVS_MENU_DESCRIPTION = MenuDescription(
    "Database Processing Menu",
    subtitle="Use this menu to get things from a database.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_CSVS_MENU_DEFAULTS = {
    "default_rotate_multipole_moments": True,
    "default_calculate_feature_forces": False,
    "default_filter_by_energy": True,
    "default_difference_iqa_wfn": 4.184,
    "default_filter_by_integration_error": True,
    "default_integration_error": 0.001,
    "default_numer_of_cores": 4,
    "default_submit_on_compute": True,
}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitCSVSMenuOptions(MenuOptions):

    selected_database_path: Path
    selected_rotate_multipole_moments: bool
    selected_calculate_feature_forces: bool
    selected_filter_by_energy: bool
    selected_difference_iqa_and_wfn_kj_per_mol: float
    selected_filter_by_integration_error: bool
    selected_integration_error: float
    selected_number_of_cores: int
    selected_submit_on_compute: bool

    def check_selected_database_path(self) -> Union[str, None]:
        """Checks whether the given database exists or if it is a file."""
        db_path = Path(self.selected_database_path)
        if not db_path.exists():
            return f"Current database path: {db_path} does not exist."
        elif not db_path.is_file():
            return f"Current database path: {db_path} is not a file."


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
    def select_filter_by_energy():
        """
        Asks user whether or not to filter the database by energy. This will filter by the difference
        of the WFN comapred to sum of IQA energy. Note the difference is in kJ mol-1
        """

        submit_csvs_menu_options.selected_filter_by_energy = user_input_bool(
            "Filter by energy (yes/no): ",
            submit_csvs_menu_options.selected_filter_by_energy,
        )
        if not submit_csvs_menu_options.selected_filter_by_energy:
            submit_csvs_menu_options.selected_difference_iqa_and_wfn_kj_per_mol = (
                math.inf
            )

    @staticmethod
    def select_difference_IQA_and_WFN_threshold():
        """
        Asks user to give a float for the maximum value of the energy difference between
        the sum of IQA for atoms and the WFN energy.

        If the absolute difference is greater than this, then the point will be
        filtered out.

        .. note::
            The IQA energy for the atoms must be calculated in order for this
            to take effect. Without IQA energy (encomp=3), we cannot do this
            comparison
        """

        if submit_csvs_menu_options.selected_filter_by_energy:
            submit_csvs_menu_options.selected_difference_iqa_and_wfn_kj_per_mol = (
                user_input_float(
                    "Absolute maximum energy difference threshold: ",
                    submit_csvs_menu_options.selected_difference_iqa_and_wfn_kj_per_mol,
                )
            )
        else:
            input("Filtering by energy is turned off. Press Enter to go back to menu.")

    @staticmethod
    def select_filter_by_integration_error():
        """
        Asks user whether or not to filter out database by integration error
        """

        submit_csvs_menu_options.selected_filter_by_integration_error = user_input_bool(
            "Filter by integration errror (yes/no): ",
            submit_csvs_menu_options.selected_filter_by_integration_error,
        )
        if not submit_csvs_menu_options.selected_filter_by_integration_error:
            submit_csvs_menu_options.selected_integration_error = math.inf

    @staticmethod
    def select_integration_error_threshold():
        """
        Asks user to select an integration error (float) above which to filter points.
        """

        if submit_csvs_menu_options.selected_filter_by_integration_error:
            submit_csvs_menu_options.selected_integration_error = user_input_float(
                "Integration error threshold: ",
                submit_csvs_menu_options.selected_integration_error,
            )
        # if filtering by integration error is off, then
        # do not make it possible to change the integration error threshold.
        else:
            input(
                "Filtering by integration error is turned off. Press Enter to go back to menu."
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
        rotate_multipole_moments = (
            submit_csvs_menu_options.selected_rotate_multipole_moments
        )
        calculate_feature_forces = (
            submit_csvs_menu_options.selected_calculate_feature_forces
        )
        float_difference_iqa_wfn = (
            submit_csvs_menu_options.selected_difference_iqa_and_wfn_kj_per_mol
        )
        float_integration_error = submit_csvs_menu_options.selected_integration_error
        ncores = submit_csvs_menu_options.selected_number_of_cores
        submit_on_compute = submit_csvs_menu_options.selected_submit_on_compute

        if not submit_on_compute:
            alf = get_alf_from_first_db_geometry(db_path)
            write_processed_data_for_atoms_parallel(
                db_path,
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
        "Change rotate multipole moments",
        SubmitCSVSFunctions.select_rotate_multipole_moments,
    ),
    FunctionItem(
        "Change calculate feature forces",
        SubmitCSVSFunctions.select_calculate_feature_forces,
    ),
    FunctionItem(
        "Change filter by energy (yes/no)",
        SubmitCSVSFunctions.select_filter_by_energy,
    ),
    FunctionItem(
        "Change energy threshold",
        SubmitCSVSFunctions.select_difference_IQA_and_WFN_threshold,
    ),
    FunctionItem(
        "Change filter by integration error",
        SubmitCSVSFunctions.select_filter_by_integration_error,
    ),
    FunctionItem(
        "Change integration error threshold",
        SubmitCSVSFunctions.select_integration_error_threshold,
    ),
    FunctionItem(
        "Change number of cores, parallelized over number of atoms",
        SubmitCSVSFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Make CSVS from database", SubmitCSVSFunctions.make_csvs_from_database
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
