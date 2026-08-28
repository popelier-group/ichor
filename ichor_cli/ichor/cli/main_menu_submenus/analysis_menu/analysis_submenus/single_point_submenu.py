"""The DL_FFLUX single points menu, a shortcut for running every geometry of an .xyz file
through DL_FFLUX as a single point calculation (no dynamics), e.g. to compare the FFLUX
predictions for a set of geometries against the reference values they were labelled with.

It is a cut down version of the robustness setup menu: the number of geometries comes from
the file rather than being asked for (though it can be capped), and the number of timesteps
is not a setting because a single point is what makes this menu what it is.
"""

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
    directory_selected,
    print_summary_and_pause,
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    xyz_file_selected,
)
from ichor.core.files import count_geometries_in_xyz
from ichor.hpc.molecular_dynamics import submit_dlpoly_fflux_single_points

# TODO: possibly make this be read from a file
SINGLE_POINT_MENU_DEFAULTS = {
    # number of geometries to calculate; 0 = every geometry in the file
    "default_number_of_geometries": 0,
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    "default_cutoff": 0.0,
    "default_number_of_cores": 1,
    # empty string means "use the executable path from the config"
    "default_executable_path": "",
}

SINGLE_POINT_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Single Points Menu",
    subtitle="Use this to run every geometry of an .xyz file through DL_FFLUX as a "
    "single point calculation.",
)


@dataclass
class SinglePointMenuOptions(MenuOptions):

    # base directory in which the per-geometry POINT* directories are created
    selected_dlpoly_single_point_path: Path
    # location of the trained models (usually one of the 6_MODEL/xxx subfolders)
    selected_model_directory_path: Path
    # .xyz file holding the geometries to calculate
    selected_trajectory_path: Path
    # number of geometries in the selected file, read from it when it is selected
    number_of_geometries_in_file: int
    # number of geometries (taken in order) to calculate; 0 = all of them
    selected_number_of_geometries: int
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    selected_cutoff: float
    # computational resources
    selected_number_of_cores: int
    # optional override of the configured DL_FFLUX (DLPOLY.Z) executable path
    selected_executable_path: str

    def check_selected_model_directory_path(self) -> Union[str, None]:
        """Checks whether the given model directory exists and is a directory."""
        model_path = Path(self.selected_model_directory_path)
        if not model_path.exists():
            return f"Current model path: {model_path} does not exist."
        elif not model_path.is_dir():
            return f"Current model path: {model_path} is not a directory."

    def check_selected_trajectory_path(self) -> Union[str, None]:
        """Checks whether the given geometries file exists and is a .xyz file."""
        traj_path = Path(self.selected_trajectory_path)
        if not traj_path.exists():
            return f"Current geometries path: {traj_path} does not exist."
        elif not traj_path.is_file():
            return f"Current geometries path: {traj_path} is not a file."
        elif traj_path.suffix != ".xyz":
            return f"Current geometries path: {traj_path} might not be a .xyz file."

    def check_selected_number_of_geometries(self) -> Union[str, None]:
        """Checks that the number of geometries to calculate is one the file can give.
        Asking for more than there are is not an error (all of them are calculated), but
        it is worth saying so before a job array of the wrong size is expected."""
        if (
            self.number_of_geometries_in_file
            and self.selected_number_of_geometries > self.number_of_geometries_in_file
        ):
            return (
                f"Only {self.number_of_geometries_in_file} geometries are in the "
                f"selected file, so {self.number_of_geometries_in_file} (not "
                f"{self.selected_number_of_geometries}) single points will be run."
            )


# initialize dataclass for storing information for menu
single_point_menu_options = SinglePointMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH,
    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH,
    0,
    SINGLE_POINT_MENU_DEFAULTS["default_number_of_geometries"],
    SINGLE_POINT_MENU_DEFAULTS["default_cutoff"],
    SINGLE_POINT_MENU_DEFAULTS["default_number_of_cores"],
    SINGLE_POINT_MENU_DEFAULTS["default_executable_path"],
)


# class with static methods for each menu item that calls a function.
class SinglePointMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_single_point_path():
        """Select the base directory in which the per-geometry POINT* directories are
        created. The models are copied into this directory once and linked to by every
        one of the calculations, so a base path which already holds calculations can only
        be used again with the same models."""
        base_path = user_input_path("Enter single points base path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH = Path(
            base_path
        ).absolute()
        single_point_menu_options.selected_dlpoly_single_point_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH
        )

    @staticmethod
    def select_model_directory_path():
        """Select the directory containing the trained models (e.g. a 6_MODEL/xxx subfolder)."""
        model_path = user_input_path("Enter model directory path: ")
        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH = Path(
            model_path
        ).absolute()
        single_point_menu_options.selected_model_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
        )

    @staticmethod
    def select_trajectory_path():
        """Select the .xyz file holding the geometries to calculate. The number of
        geometries in it is counted (without reading them all in) so that the number of
        single points does not have to be given by hand."""
        traj_path = user_input_path("Enter geometries .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH = (
            Path(traj_path).absolute()
        )
        single_point_menu_options.selected_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH
        )

        try:
            single_point_menu_options.number_of_geometries_in_file = (
                count_geometries_in_xyz(
                    single_point_menu_options.selected_trajectory_path
                )
            )
        except (OSError, ValueError):
            # an unreadable file (or one which is not an xyz) is caught by the check
            # functions, which say so in the menu prologue
            single_point_menu_options.number_of_geometries_in_file = 0

    @staticmethod
    def select_number_of_geometries():
        """Select how many of the geometries in the file (taken in order) to calculate.
        Enter 0 to calculate every geometry in it, which is what this menu is for; a
        smaller number is useful to try a handful of them out first."""
        single_point_menu_options.selected_number_of_geometries = user_input_int(
            "Select number of geometries to calculate (0 = all in the file): ",
            single_point_menu_options.selected_number_of_geometries,
        )

    @staticmethod
    def select_cutoff():
        """Select the real-space cutoff (in Angstrom) for the CONTROL cutoff/rvdw and the
        FFLUX.in electrostatics cut directives. Enter 0 to auto-derive it from the geometry
        (largest interatomic distance + margin), which is a good default for a single molecule
        or small cluster; set an explicit value (e.g. 8-12) for condensed-phase boxes."""
        single_point_menu_options.selected_cutoff = user_input_float(
            "Select real-space cutoff in Angstrom (0 = auto from geometry): ",
            single_point_menu_options.selected_cutoff,
        )

    @staticmethod
    def select_number_of_cores():
        """Select the number of cores to use per single point calculation."""
        single_point_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ",
            single_point_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_executable_path():
        """Select an optional DL_FFLUX (DLPOLY.Z) executable path that overrides the
        path configured in the ichor config file. Leave blank to use the configured path."""
        single_point_menu_options.selected_executable_path = user_input_free_flow(
            "Enter DL_FFLUX executable path (blank = use config): ",
            single_point_menu_options.selected_executable_path,
        )

    @staticmethod
    def submit_single_points_to_compute():
        """Sets up one POINT* directory per geometry, all linking to the one copy of the
        models kept in the base path, and submits them as a job array."""

        # every path defaults to the directory ichor is running in, so without these the
        # calculations are set up next to wherever ichor was started, with no models
        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH,
            "submit the single point calculations",
            what="single points base path",
            # the base path is made if it is not there, so only the choice of it matters
            must_exist=False,
            select_with="Use 'Select single points base path' in this menu first.",
        ):
            return

        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
            "submit the single point calculations",
            what="model directory",
            select_with="Use 'Select model directory' in this menu to select the "
            "folder of trained models to calculate with.",
        ):
            return

        if not xyz_file_selected(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH,
            "submit the single point calculations",
            what="geometries file",
            select_with="Use 'Select geometries (.xyz file to calculate every geometry "
            "of)' in this menu first.",
        ):
            return

        try:
            job_id = submit_dlpoly_fflux_single_points(
                base_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH,  # noqa: E501
                model_directory=ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,  # noqa: E501
                trajectory_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH,  # noqa: E501
                # 0 means every geometry in the file
                ngeometries=single_point_menu_options.selected_number_of_geometries
                or None,
                cutoff=single_point_menu_options.selected_cutoff or None,
                ncores=single_point_menu_options.selected_number_of_cores,
                executable_path=single_point_menu_options.selected_executable_path
                or None,
            )
        except ValueError as error:
            # e.g. the base path already holds calculations sharing a different set of
            # models, which is worth saying rather than crashing out of the menu
            ichor.hpc.global_variables.LOGGER.error(
                f"DL_FFLUX single points not submitted: {error}"
            )
            print_summary_and_pause(
                "DL_FFLUX SINGLE POINTS NOT SUBMITTED",
                {
                    "Base path": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH  # noqa: E501
                    ),
                    "Model directory": (
                        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
                    ),
                    "Reason": error,
                },
                [
                    "Every calculation under one base path shares the single copy of "
                    "the models kept there, so a base path can only be reused with the "
                    "models it already holds. Pick an empty (or new) base path to use "
                    "a different set of models.",
                ],
            )
            return

        ngeometries = single_point_menu_options.selected_number_of_geometries
        cutoff = single_point_menu_options.selected_cutoff

        print_summary_and_pause(
            "DL_FFLUX SINGLE POINTS SUBMITTED",
            {
                "Base path": (
                    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_PATH
                ),
                "Model directory": (
                    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
                ),
                "Trajectory": (
                    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SINGLE_POINT_TRAJECTORY_PATH  # noqa: E501
                ),
                "Job ID": job_id.id if job_id else "not available",
                "Geometries": (
                    f"{ngeometries:,}" if ngeometries else "every geometry in the file"
                ),
                "Cutoff": (
                    f"{cutoff} Angstrom" if cutoff else "auto (from the geometry)"
                ),
                "CPU cores per point": (
                    single_point_menu_options.selected_number_of_cores
                ),
                "Executable": (
                    single_point_menu_options.selected_executable_path or "from config"
                ),
            },
            [
                "No dynamics is run: each geometry gets its own POINT<i> directory and "
                "a zero-timestep run, so DL_FFLUX simply evaluates the geometry it was "
                "given and stops.",
                "All of the points were submitted together as one job array, so check "
                "on them with your batch system's queue command (e.g. qstat / squeue).",
                "The FFLUX energies (and forces) of each geometry end up in its POINT "
                "directory, which is what you compare against the Gaussian/AIMAll "
                "values the geometries were labelled with.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info("DL_FFLUX single point jobs submitted")


# initialize menu
single_point_menu = ConsoleMenu(
    this_menu_options=single_point_menu_options,
    title=SINGLE_POINT_MENU_DESCRIPTION.title,
    subtitle=SINGLE_POINT_MENU_DESCRIPTION.subtitle,
    prologue_text=SINGLE_POINT_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SINGLE_POINT_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SINGLE_POINT_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
single_point_menu_items = [
    FunctionItem(
        "Select single points base path (POINT0, POINT1, ... are created inside it)",
        SinglePointMenuFunctions.select_single_point_path,
    ),
    FunctionItem(
        "Select model directory (e.g. a 6_MODEL/xxx subfolder)",
        SinglePointMenuFunctions.select_model_directory_path,
    ),
    FunctionItem(
        "Select geometries (.xyz file to calculate every geometry of)",
        SinglePointMenuFunctions.select_trajectory_path,
    ),
    FunctionItem(
        "Select number of geometries (0 = all in the file)",
        SinglePointMenuFunctions.select_number_of_geometries,
    ),
    FunctionItem(
        "Select real-space cutoff (Angstrom, 0 = auto)",
        SinglePointMenuFunctions.select_cutoff,
    ),
    FunctionItem(
        "Select number of cores",
        SinglePointMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Select DL_FFLUX executable path (optional override)",
        SinglePointMenuFunctions.select_executable_path,
    ),
    FunctionItem(
        "Set up and submit DL_FFLUX single points to compute",
        SinglePointMenuFunctions.submit_single_points_to_compute,
    ),
]

add_items_to_menu(single_point_menu, single_point_menu_items)
