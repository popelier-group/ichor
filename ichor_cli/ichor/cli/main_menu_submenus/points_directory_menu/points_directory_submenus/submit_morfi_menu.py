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
from ichor.hpc.main import submit_points_directory_to_gaussian
from ichor.hpc.submission_commands import GaussianCommand

AVAILABLE_GRIDS = {
    "coarse": [20, 20],
    "medium": [44, 70],
    "fine": [50, 100],
}

SUBMIT_MORFI_MENU_DESCRIPTION = MenuDescription(
    "Submit Morfi Menu",
    subtitle="Use this menu to submit a PointsDirectory for electron correlation calculations.\n",
)

SUBMIT_MORFI_MENU_DEFAULTS = {
    "default_basis_set": "cc-pwCVTZ",
    "default_ncores": 16,
    "default_ngeoms": 100,
    "default_grid": [44, 70],
}


# dataclass used to store values for SubmitMorfiMenu
@dataclass
class SubmitMorfiMenuOptions(MenuOptions):

    selected_basis_set: str
    selected_number_of_cores: int
    selected_number_of_geoms: int
    selected_grid: list[int]

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

    def find_atoms(self):
        """Finds and returns a list of unique atom types for the selected PointsDir."""
        pd_path = Path(self.selected_points_directory_path)

        # Find the first XYZ file
        try:
            first_geom = next(pd_path.rglob("*.xyz"))
        except StopIteration:
            raise FileNotFoundError(f"No XYZ files found in {pd_path}")

        atom_types = []

        with open(first_geom, "r") as f:
            lines = f.readlines()

        # Skip atom count and comment line
        for line in lines[2:]:
            atom = line.split()[0]

        if atom not in atom_types:
            atom_types.append(atom)

        return atom_types


# initialize dataclass for storing information for menu
submit_morfi_menu_options = SubmitMorfiMenuOptions(*SUBMIT_MORFI_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class SubmitMorfiFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_points_directory():
        """Asks user to update points directory and then updates PointsDirectoryMenuOptions instance."""
        pd_path = user_input_path("Change PointsDirectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH = Path(
            pd_path
        ).absolute()
        submit_morfi_menu_options.selected_points_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
        )

    @staticmethod
    def select_basis_set():
        """Asks user to update the basis set."""
        submit_morfi_menu_options.selected_basis_set = user_input_free_flow(
            "Enter basis set: ", submit_morfi_menu_options.selected_basis_set
        )

    @staticmethod
    def select_number_of_cores():
        """Asks user to update the number of cores."""
        submit_morfi_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_morfi_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_grid():
        """Asks user to update the grid."""

        choice_map = {
            "1": "coarse",
            "2": "medium",
            "3": "fine",
            "4": "custom",
        }

        while True:
            choice = input(
                "Select grid:\n"
                "1. Coarse (20-20)\n"
                "2. Medium (44-70)\n"
                "3. Fine (50-100)\n"
                "4. Custom\n"
                "Enter choice (1-4): "
            ).strip()

            if choice in ("1", "2", "3"):
                break

            elif choice == "4":
                while True:
                    try:
                        ang = int(input("Enter Angular grid size: "))
                        rad = int(input("Enter Radial grid size: "))

                        if ang <= 0 or rad <= 0:
                            print("Grid size must be positive integers.")
                            continue

                        submit_morfi_menu_options.selected_grid = (ang, rad)
                        return

                    except ValueError:
                        print("Invalid input. Please enter positive integers.")
            else:
                print("Invalid input. Please enter a number between 1 and 4.")

        grid_choice = choice_map[choice]
        grid = AVAILABLE_GRIDS[grid_choice]

        submit_morfi_menu_options.selected_grid = grid

    @staticmethod
    def points_directory_to_morfi_on_compute():
        """Submits a single PointsDirectory to Morfi on compute."""
        print("STARTING MORFI JOB SUBMISSION\n")

        basis_set, ncores, ngeoms, grid = (
            submit_morfi_menu_options.selected_basis_set,
            submit_morfi_menu_options.selected_number_of_cores,
            submit_morfi_menu_options.selected_number_of_geometries,
            submit_morfi_menu_options.selected_grid,
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

                submit_points_directory_to_gaussian(
                    points_directory=pd,
                    basis_set=basis_set,
                    ncores=ncores,
                    ngeoms=ngeoms,
                    grid=grid,
                    outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE[
                        "outputs"
                    ]
                    / pd.path.name
                    / "MORFI",
                    errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                    / pd.path.name
                    / "MORFI",
                )

        # if containing one PointsDirectory
        else:
            pd = PointsDirectory(
                ichor.cli.global_menu_variables.SELECTED_POINTS_DIRECTORY_PATH
            )

            submit_points_directory_to_gaussian(
                points_directory=pd,
                basis_set=basis_set,
                ncores=ncores,
                ngeoms=ngeoms,
                grid=grid,
                outputs_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["outputs"]
                / pd.path.name
                / "MORFI",
                errors_dir_path=ichor.hpc.global_variables.FILE_STRUCTURE["errors"]
                / pd.path.name
                / "MORFI",
            )
        answer = ""
        user_input_free_flow(
            "MORFI JOB SUBMITTED. Press enter to continue: ",
            answer,
        )


# make menu items
# can use lambda functions to change text of options as well :)
submit_morfi_menu_items = [
    FunctionItem(
        "Select PointsDirectory Path or Parent to PointsDirectory",
        SubmitMorfiFunctions.select_points_directory,
    ),
    FunctionItem("Select Basis Set", SubmitMorfiFunctions.select_basis_set),
    FunctionItem("Select Number of Cores", SubmitMorfiFunctions.select_number_of_cores),
    FunctionItem(
        "Select Number of Geometries", SubmitMorfiFunctions.select_number_of_geoms
    ),
    FunctionItem("Select Grid", SubmitMorfiFunctions.select_grid),
    FunctionItem(
        "Submit to Morfi on compute",
        SubmitMorfiFunctions.points_directory_to_gaussian_on_compute,
    ),
]

# initialize menu
submit_morfi_menu = ConsoleMenu(
    this_menu_options=submit_morfi_menu_options,
    title=SUBMIT_MORFI_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_MORFI_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_MORFI_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_MORFI_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_MORFI_MENU_DESCRIPTION.show_exit_option,
)

add_items_to_menu(submit_morfi_menu, submit_morfi_menu_items)
