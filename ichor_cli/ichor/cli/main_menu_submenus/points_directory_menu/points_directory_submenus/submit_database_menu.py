from dataclasses import dataclass, field
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_bool,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.core.files import PointsDirectory, PointsDirectoryParent
from ichor.core.useful_functions import single_or_many_points_directories
from ichor.hpc.main.database import AVAILABLE_DATABASE_FORMATS, submit_make_database

SUBMIT_DATABASE_MENU_DESCRIPTION = MenuDescription(
    "Database Menu",
    subtitle="Use this menu to make a database from PointsDirectory.\n",
)

# TODO: possibly make this be read from a file
SUBMIT_DATABASE_MENU_DEFAULTS = {
    "default_database_format": "sqlite",
    "default_ncores": 1,
    "default_submit_on_compute": True,
}


# dataclass used to store values for SubmitAIMALLMenu
@dataclass
class SubmitDatabaseMenuOptions(MenuOptions):

    selected_database_format: str
    selected_number_of_cores: int
    selected_submit_on_compute: bool
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
submit_database_menu_options = SubmitDatabaseMenuOptions(
    *SUBMIT_DATABASE_MENU_DEFAULTS.values()
)


# class with static methods for each menu item that calls a function.
class SubmitDatabaseFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_database_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def select_database():
        """Asks user to update the method for AIMALL. The method
        needs to be added to the WFN file so that AIMALL does the correct
        calculation."""

        submit_database_menu_options.selected_database_format = user_input_restricted(
            AVAILABLE_DATABASE_FORMATS.keys(),
            "Choose a database format: ",
            submit_database_menu_options.selected_database_format,
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to select number of cores."""
        submit_database_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_database_menu_options.selected_number_of_cores,
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
        and works for one `PointsDirectory` or parent directory containing many `PointsDirectory`-ies
        """

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )
        )

        database_format, ncores, submit_on_compute = (
            submit_database_menu_options.selected_database_format,
            submit_database_menu_options.selected_number_of_cores,
            submit_database_menu_options.selected_submit_on_compute,
        )

        # this is used to be able to call the respective methods from PointsDirectory
        # so that the same code below is used with the respective methods
        str_database_method = AVAILABLE_DATABASE_FORMATS[database_format]

        points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )
        contents = (
            "many PointsDirectory-ies"
            if is_parent_directory_to_many_points_directories
            else "one PointsDirectory"
        )

        if submit_on_compute:

            job_id = submit_make_database(
                points_directory_path,
                database_format,
                ncores=ncores,
            )

            print_summary_and_pause(
                "DATABASE JOB SUBMITTED",
                {
                    "PointsDirectory": points_directory_path,
                    "Contents": contents,
                    "Database format": database_format,
                    "Database": points_directory_path / points_directory_path.stem,
                    "Job ID": job_id.id if job_id else "not available",
                    "CPU cores": ncores,
                    "Ran on": "compute node",
                },
                [
                    "The database collects the geometries and the Gaussian/AIMAll "
                    "results of every point into one place, so it is worth running "
                    "only once those calculations have finished; any point missing "
                    "data is reported in the job's output.",
                    "The job is now queued, so it will not start immediately and this "
                    "menu does not wait for it. Check on it with your batch system's "
                    "queue command (e.g. qstat / squeue).",
                    "The database is written inside the PointsDirectory and named after "
                    "it (with the format's own suffix). Use 'Make csvs from database' "
                    "afterwards to get the training data out of it.",
                ],
            )
            return

        # pointsdirectory parent json on login
        if is_parent_directory_to_many_points_directories:
            pointsdirparent = PointsDirectoryParent(points_directory_path)
            func = getattr(pointsdirparent, str_database_method)
            database_path = func(print_missing_data=True)
        else:
            pointdir = PointsDirectory(points_directory_path)
            func = getattr(pointdir, str_database_method)
            database_path = func(print_missing_data=True)

        print_summary_and_pause(
            "DATABASE WRITTEN",
            {
                "PointsDirectory": points_directory_path,
                "Contents": contents,
                "Database format": database_format,
                "Database": database_path if database_path else "see messages above",
                "Ran on": "login node (not submitted)",
            },
            [
                "The database was made here and now rather than on a compute node, so "
                "it is already finished. Any point that was missing Gaussian or AIMAll "
                "data is listed above.",
                "Use 'Make csvs from database' to turn the database into the feature "
                "and property csv files that model training reads.",
            ],
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_database_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        SubmitDatabaseFunctions.select_points_directory,
    ),
    FunctionItem(
        "Change database format",
        SubmitDatabaseFunctions.select_database,
    ),
    FunctionItem(
        "Change number of cores",
        SubmitDatabaseFunctions.select_number_of_cores,
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
