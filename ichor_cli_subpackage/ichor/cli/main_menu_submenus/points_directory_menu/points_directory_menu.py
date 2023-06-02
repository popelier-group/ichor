from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.script_names import SCRIPT_NAMES
from ichor.cli.useful_functions import (
    bool_to_str,
    compile_strings_to_python_code,
    user_input_bool,
    user_input_free_flow,
    user_input_int,
    user_input_path,
)
from ichor.core.files import PointsDirectory
from ichor.hpc.main import (
    submit_points_directory_to_aimall,
    submit_points_directory_to_gaussian,
)
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript


def ask_user_for_gaussian_settings():

    default_method = "b3lyp"
    default_basis_set = "6-31+g(d,p)"
    default_number_of_cores = 2
    default_overwrite_existing = False
    default_force_calculate_wfn = False

    method = user_input_free_flow(
        f"Method for Gaussian calculations, default {default_method}: "
    )
    if method is None:
        method = default_method

    basis_set = user_input_free_flow(
        f"Basis set for Gaussian calculations, default {default_basis_set}: "
    )
    if basis_set is None:
        basis_set = default_basis_set

    ncores = user_input_int(
        f"Number of cores for Gaussian calculations, default {default_number_of_cores}: "
    )
    if ncores is None:
        ncores = default_number_of_cores

    overwrite_existing = user_input_bool(
        f"Overwrite existing GJFs (yes/no), default {bool_to_str(default_overwrite_existing)}: "
    )
    if overwrite_existing is None:
        overwrite_existing = default_overwrite_existing

    force_calculate_wfn = user_input_bool(
        f"Recalculate if wfn already exists (yes/no), default {bool_to_str(default_force_calculate_wfn)}: "
    )
    if force_calculate_wfn is None:
        force_calculate_wfn = default_force_calculate_wfn

    return method, basis_set, ncores, overwrite_existing, force_calculate_wfn


def ask_user_for_aimall_settings():

    default_method = "b3lyp"
    default_number_of_cores = 2
    default_naat = 1
    default_encomp = 3

    method = user_input_free_flow(
        f"Method to be used for AIMAll calculations, default {default_method}: "
    )
    if method is None:
        method = default_method

    ncores = user_input_int(
        f"Number of cores for AIMAll calculations, default {default_number_of_cores}: "
    )
    if ncores is None:
        ncores = default_number_of_cores

    naat = user_input_int(
        f"Number of atoms at a time in AIMAll, default {default_naat}: "
    )
    if naat is None:
        naat = default_naat

    encomp = user_input_int(f"AIMAll -encomp setting, default {default_encomp}: ")
    if encomp is None:
        encomp = default_encomp

    return method, ncores, naat, encomp


def single_or_many_points_directories():
    """Checks whether the current selected PointsDirectory path is a directory containing
    many PointsDirectories, or is just one PointsDirectory.

    This is just done by checking if parent is in the name of the directory.
    """

    if (
        "parent"
        in ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem.lower()
    ):
        return True
    return False


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
            return f"Current path: {pd_path} does not exist or is not a directory."


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
    def points_directory_to_gaussian_on_compute():
        """Submits a single PointsDirectory to Gaussian on compute."""

        (
            method,
            basis_set,
            ncores,
            overwrite_existing,
            force_calculate_wfn,
        ) = ask_user_for_gaussian_settings()

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories()
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
            )

    @staticmethod
    def points_directory_to_aimall_on_compute():
        """Submits a single PointsDirectory to AIMAll on compute."""

        method, ncores, naat, encomp = ask_user_for_aimall_settings()

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories()
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
            )

    @staticmethod
    def points_directory_to_database():
        """Converts the current given PointsDirectory to a SQLite3 database."""

        default_submit_on_compute = True

        submit_on_compute = user_input_bool(
            f"Submit to compute node (yes/no), default {bool_to_str(default_submit_on_compute)}: "
        )
        if submit_on_compute is None:
            submit_on_compute = default_submit_on_compute

        is_parent_directory_to_many_points_directories = (
            single_or_many_points_directories()
        )

        # if running on login node, discouraged because takes a long time
        if not submit_on_compute:

            # if running on a directory containing many PointsDirectories
            if is_parent_directory_to_many_points_directories:

                for (
                    d
                ) in (
                    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.iterdir()
                ):

                    pd = PointsDirectory(d)
                    # write all data to a single database by passing in the same name for every PointsDirectory
                    pd.write_to_sqlite3_database(
                        f"{ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem}_sqlite.db"
                    )

            else:
                pd = PointsDirectory(
                    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
                )
                pd.write_to_sqlite3_database()

        else:

            # if turning many PointsDirectories into db on compute node
            if is_parent_directory_to_many_points_directories:

                db_name = (
                    ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.stem
                    + "_sqlite.db"
                )

                text_list = []
                # make the python command that will be written in the submit script
                # it will get executed as `python -c python_code_to_execute...`
                text_list.append("from ichor.core.files import PointsDirectory")
                str_part1 = "for d in ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH.iterdir():"
                str_part2 = " PointsDirectory(d).write_to_sqlite3_database("
                str_part3 = f"'{db_name}', print_missing_data=True)"

                total_str = str_part1 + str_part2 + str_part3

                text_list.append(total_str)
                final_cmd = compile_strings_to_python_code(text_list)
                py_cmd = FreeFlowPythonCommand(final_cmd)
                with SubmissionScript(
                    SCRIPT_NAMES["pd_to_sqlite3"], ncores=8
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
                text_list.append(
                    "pd.write_to_sqlite3_database(print_missing_data=True)"
                )

                final_cmd = compile_strings_to_python_code(text_list)
                py_cmd = FreeFlowPythonCommand(final_cmd)
                with SubmissionScript(
                    SCRIPT_NAMES["pd_to_sqlite3"], ncores=8
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
        "Select path of PointsDirectory or Parent to many PointsDirectory",
        PointsDirectoryFunctions.select_points_directory,
    ),
    FunctionItem(
        "Submit to Gaussian",
        PointsDirectoryFunctions.points_directory_to_gaussian_on_compute,
    ),
    FunctionItem(
        "Submit to AIMAll",
        PointsDirectoryFunctions.points_directory_to_aimall_on_compute,
    ),
    FunctionItem(
        "Make into SQLite3 database",
        PointsDirectoryFunctions.points_directory_to_database,
    ),
]

add_items_to_menu(points_directory_menu, point_directory_menu_items)
