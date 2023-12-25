from dataclasses import dataclass

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.script_names import SCRIPT_NAMES
from ichor.cli.useful_functions import (
    compile_strings_to_python_code,
    single_or_many_points_directories,
    user_input_bool,
    user_input_restricted,
)
from ichor.core.files import PointsDirectory
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript

SUBMIT_DATABASE_MENU_DESCRIPTION = MenuDescription(
    "Database Menu",
    subtitle="Use this menu to make a database from PointsDirectory.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_DATABASE_MENU_DEFAULTS = {
    "default_database_format": "sqlite",
    "default_submit_on_compute": True,
}

AVAILABLE_DATABASE_FORMATS = {"sqlite": "write_to_sqlite3_database"}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitDatabaseMenuOptions(MenuOptions):

    selected_database_format: str
    selected_submit_on_compute: bool


# initialize dataclass for storing information for menu
submit_database_menu_options = SubmitDatabaseMenuOptions(
    *SUBMIT_DATABASE_MENU_DEFAULTS.values()
)


def make_database(database_format, submit_on_compute):

    is_parent_directory_to_many_points_directories = single_or_many_points_directories()

    # this is used to be able to call the respective methods from PointsDirectory
    # so that the same code below is used with the respective methods
    str_database_method = AVAILABLE_DATABASE_FORMATS[database_format]

    # if running on login node, discouraged because takes a long time
    if not submit_on_compute:

        # if running on a directory containing many PointsDirectories
        if is_parent_directory_to_many_points_directories:

            db_name = (
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem
                + f"_{database_format}.db"
            )

            for (
                d
            ) in (
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.iterdir()
            ):

                pd = PointsDirectory(d)
                # write all data to a single database by passing in the same name for every PointsDirectory
                getattr(pd, str_database_method)(db_name)

        else:
            pd = PointsDirectory(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )
            getattr(pd, str_database_method)()

    # if running on compute node
    else:

        # if turning many PointsDirectories into db on compute node
        if is_parent_directory_to_many_points_directories:

            db_name = (
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem
                + f"_{database_format}.db"
            )

            text_list = []
            # make the python command that will be written in the submit script
            # it will get executed as `python -c python_code_to_execute...`
            text_list.append("from ichor.core.files import PointsDirectory")
            text_list.append("from pathlib import Path")
            # make the parent directory path in a Path object
            text_list.append(
                f"parent_dir = Path('{ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH}')"
            )

            # make a list comprehension that writes each PointsDirectory in the parent dir
            # into the same SQLite database
            # needs to be a list comprehension because for loops do not work with -c flag
            str_part1 = f"[PointsDirectory(d).{str_database_method}('{db_name}', print_missing_data=True)"
            str_part2 = " for d in parent_dir.iterdir()]"

            total_str = str_part1 + str_part2

            text_list.append(total_str)
            final_cmd = compile_strings_to_python_code(text_list)
            py_cmd = FreeFlowPythonCommand(final_cmd)
            with SubmissionScript(
                SCRIPT_NAMES["pd_to_database"], ncores=1
            ) as submission_script:
                submission_script.add_command(py_cmd)
            submission_script.submit()

        # if only one PointsDirectory to sql on compute
        else:

            text_list = []
            # make the python command that will be written in the submit script
            # it will get executed as `python -c python_code_to_execute...`
            text_list.append("from ichor.core.files import PointsDirectory")
            text_list.append(
                f"pd = PointsDirectory('{ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH}')"
            )
            text_list.append(f"pd.{str_database_method}(print_missing_data=True)")

            final_cmd = compile_strings_to_python_code(text_list)
            py_cmd = FreeFlowPythonCommand(final_cmd)
            with SubmissionScript(
                SCRIPT_NAMES["pd_to_database"], ncores=1
            ) as submission_script:
                submission_script.add_command(py_cmd)
            submission_script.submit()


# class with static methods for each menu item that calls a function.
class SubmitDatabaseFunctions:
    @staticmethod
    def select_database():
        """Asks user to update the ethod for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_database_menu_options.selected_database_format = user_input_restricted(
            AVAILABLE_DATABASE_FORMATS.keys(),
            "Choose a database format: ",
            submit_database_menu_options.selected_database_format,
        )

    @staticmethod
    def select_submit_on_compute():
        """
        Asks user whether or not to submit database making on compute.
        """

        submit_database_menu_options.selected_submit_on_compute = user_input_bool(
            "Submit on compute (yes/no): ",
            submit_database_menu_options.selected_submit_on_compute,
        )

    @staticmethod
    def points_directory_to_database():
        """Converts the current given PointsDirectory to a SQLite3 database. Can be submitted on compute
        and works for one `PointsDirectory` or parent directory containing many `PointsDirectory`-ies"""

        database_format, submit_on_compute = (
            submit_database_menu_options.selected_database,
            submit_database_menu_options.selected_submit_on_compute,
        )

        make_database(database_format, submit_on_compute)


# make menu items
# can use lambda functions to change text of options as well :)
submit_database_menu_items = [
    FunctionItem(
        "Change database format",
        SubmitDatabaseFunctions.select_database,
    ),
    FunctionItem(
        "Change submit to compute",
        SubmitDatabaseFunctions.select_submit_on_compute,
    ),
    FunctionItem(
        "Make database",
        SubmitDatabaseFunctions.points_directory_to_database,
    ),
]

# initialize menu
submit_database_menu = ConsoleMenu(
    this_menu_options=submit_database_menu_options,
    title=SUBMIT_DATABASE_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_DATABASE_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_DATABASE_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_DATABASE_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_DATABASE_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_database_menu, submit_database_menu_items)
