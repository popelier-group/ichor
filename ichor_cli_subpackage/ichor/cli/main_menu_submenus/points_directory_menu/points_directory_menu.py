from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.script_names import SCRIPT_NAMES
from ichor.cli.useful_functions import compile_strings_to_python_code
from ichor.cli.useful_functions.user_input import user_input_bool, user_input_path
from ichor.core.files import PointsDirectory
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript


POINTS_DIRECTORY_MENU_DESCRIPTION = MenuDescription(
    "PointsDirectory Menu",
    subtitle="Use this to interact with ichor's PointsDirectory class.\n",
)


# dataclass used to store values for PointsDirectoryMenu
@dataclass
class PointsDirectoryMenuOptions(MenuOptions):
    # defaults to the current working directory
    selected_points_directory_path: Path = (
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
    )

    def check_selected_points_directory_path(self) -> Union[str, None]:
        """Checks whether the given PointsDirectory exists or if it is a directory."""
        pd_path = Path(self.selected_points_directory_path)
        if (not pd_path.exists()) or (not pd_path.is_dir()):
            return f"Current {pd_path} does not exist or is not a directory."


# initialize dataclass for storing information for menu
points_directory_menu_options = PointsDirectoryMenuOptions()


# class with static methods for each menu item that calls a function.
class PointsDirectoryFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuPrologue instance."""
        pd_path = user_input_path("Enter PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        points_directory_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def points_directory_to_database():
        """Converts the current given PointsDirectory to a SQLite3 database."""

        submit_on_compute = user_input_bool("Submit to compute (yes/no), default yes: ")

        if not submit_on_compute:
            pd = pd = PointsDirectory(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )
            pd.write_to_sqlite3_database()

        else:
            text_list = []
            text_list.append("from ichor.core.files import PointsDirectory")
            text_list.append(
                f"pd = PointsDirectory('{ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH}')"
            )
            text_list.append("pd.write_to_sqlite3_database(print_missing_data=True)")

            final_cmd = compile_strings_to_python_code(text_list)
            py_cmd = FreeFlowPythonCommand(final_cmd)
            with SubmissionScript(
                SCRIPT_NAMES["pd_to_sqlite3"], ncores=4
            ) as submission_script:
                submission_script.add_command(py_cmd)
            submission_script.submit()


# initialize menu
points_directory_menu = ConsoleMenu(
    this_menu_options=points_directory_menu_options,
    title=POINTS_DIRECTORY_MENU_DESCRIPTION.title,
    subtitle=POINTS_DIRECTORY_MENU_DESCRIPTION.subtitle,
    prologue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=POINTS_DIRECTORY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=POINTS_DIRECTORY_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
point_directory_menu_items = [
    FunctionItem(
        "Select path of PointsDirectory",
        PointsDirectoryFunctions.select_points_directory,
    ),
    FunctionItem(
        "Make PointsDirectory into SQLite3 database.",
        PointsDirectoryFunctions.points_directory_to_database,
    ),
]

add_items_to_menu(points_directory_menu, point_directory_menu_items)
