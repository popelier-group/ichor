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
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.hpc.molecular_dynamics import submit_dlpoly_fflux_robustness

# available DL_POLY ensembles that the menu exposes
ROBUSTNESS_ENSEMBLES = ["nvt", "nve"]

# TODO: possibly make this be read from a file
ROBUSTNESS_MENU_DEFAULTS = {
    "default_number_of_seeds": 10,
    "default_ensemble": "nvt",
    "default_temperature": 300,
    "default_timestep": 0.001,
    "default_number_of_timesteps": 500,
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    "default_force_cap": 0.0,
    "default_number_of_cores": 1,
    # empty string means "use the executable path from the config"
    "default_executable_path": "",
}

ROBUSTNESS_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Robustness Menu",
    subtitle="Use this to run DL_FFLUX simulations from diverse seed geometries "
    "to check model robustness (e.g. explosions / implosions).",
)


@dataclass
class RobustnessMenuOptions(MenuOptions):
    # base directory in which the per-seed RUN* directories are created
    selected_dlpoly_robustness_path: Path
    # location of the trained models (usually one of the 6_MODEL/xxx subfolders)
    selected_model_directory_path: Path
    # diversity-sampled trajectory (.xyz) from which the seed geometries are taken
    selected_seed_trajectory_path: Path
    # number of seed geometries (taken in order from the trajectory)
    selected_number_of_seeds: int
    # DL_POLY calculation parameters
    selected_ensemble: str
    selected_temperature: int
    selected_timestep: float
    selected_number_of_timesteps: int
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    selected_force_cap: float
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

    def check_selected_seed_trajectory_path(self) -> Union[str, None]:
        """Checks whether the given seed trajectory exists and is a .xyz file."""
        traj_path = Path(self.selected_seed_trajectory_path)
        if not traj_path.exists():
            return f"Current seed trajectory path: {traj_path} does not exist."
        elif not traj_path.is_file():
            return f"Current seed trajectory path: {traj_path} is not a file."
        elif traj_path.suffix != ".xyz":
            return f"Current seed trajectory path: {traj_path} might not be a .xyz file."


# initialize dataclass for storing information for menu
robustness_menu_options = RobustnessMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH,
    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH,
    ROBUSTNESS_MENU_DEFAULTS["default_number_of_seeds"],
    ROBUSTNESS_MENU_DEFAULTS["default_ensemble"],
    ROBUSTNESS_MENU_DEFAULTS["default_temperature"],
    ROBUSTNESS_MENU_DEFAULTS["default_timestep"],
    ROBUSTNESS_MENU_DEFAULTS["default_number_of_timesteps"],
    ROBUSTNESS_MENU_DEFAULTS["default_force_cap"],
    ROBUSTNESS_MENU_DEFAULTS["default_number_of_cores"],
    ROBUSTNESS_MENU_DEFAULTS["default_executable_path"],
)


# class with static methods for each menu item that calls a function.
class RobustnessMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_robustness_path():
        """Select the base directory in which the per-seed RUN* directories are created."""
        base_path = user_input_path("Enter robustness base path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH = Path(
            base_path
        ).absolute()
        robustness_menu_options.selected_dlpoly_robustness_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH
        )

    @staticmethod
    def select_model_directory_path():
        """Select the directory containing the trained models (e.g. a 6_MODEL/xxx subfolder)."""
        model_path = user_input_path("Enter model directory path: ")
        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH = Path(
            model_path
        ).absolute()
        robustness_menu_options.selected_model_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
        )

    @staticmethod
    def select_seed_trajectory_path():
        """Select the diversity-sampled trajectory (.xyz) that the seeds are taken from."""
        traj_path = user_input_path("Enter seed trajectory .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH = Path(
            traj_path
        ).absolute()
        robustness_menu_options.selected_seed_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH
        )

    @staticmethod
    def select_number_of_seeds():
        """Select how many seed geometries (taken in order) to run."""
        robustness_menu_options.selected_number_of_seeds = user_input_int(
            "Select number of seed geometries: ",
            robustness_menu_options.selected_number_of_seeds,
        )

    @staticmethod
    def select_ensemble():
        """Select the DL_POLY ensemble (NVT or NVE)."""
        robustness_menu_options.selected_ensemble = user_input_restricted(
            ROBUSTNESS_ENSEMBLES,
            "Select ensemble: ",
            robustness_menu_options.selected_ensemble,
        )

    @staticmethod
    def select_temperature():
        """Select the temperature of the simulations."""
        robustness_menu_options.selected_temperature = user_input_int(
            "Select temperature: ", robustness_menu_options.selected_temperature
        )

    @staticmethod
    def select_timestep():
        """Select the timestep (in ps) of the simulations."""
        robustness_menu_options.selected_timestep = user_input_float(
            "Select timestep (ps): ", robustness_menu_options.selected_timestep
        )

    @staticmethod
    def select_number_of_timesteps():
        """Select the number of timesteps of the simulations."""
        robustness_menu_options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps: ",
            robustness_menu_options.selected_number_of_timesteps,
        )

    @staticmethod
    def select_force_cap():
        """Select the force cap (in kT/Angstrom) applied during equilibration. This keeps a
        far-from-equilibrium run (e.g. one using inaccurate FFLUX models) from exploding.
        Enter 0 to disable force capping."""
        robustness_menu_options.selected_force_cap = user_input_float(
            "Select force cap in kT/Angstrom (0 = disabled): ",
            robustness_menu_options.selected_force_cap,
        )

    @staticmethod
    def select_number_of_cores():
        """Select the number of cores to use per run."""
        robustness_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ",
            robustness_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_executable_path():
        """Select an optional DL_FFLUX (DLPOLY.Z) executable path that overrides the
        path configured in ichor_config.yaml. Leave blank to use the configured path."""
        robustness_menu_options.selected_executable_path = user_input_free_flow(
            "Enter DL_FFLUX executable path (blank = use config): ",
            robustness_menu_options.selected_executable_path,
        )

    @staticmethod
    def submit_robustness_to_compute():
        """Sets up one RUN* directory per seed geometry and submits them as a job array."""

        submit_dlpoly_fflux_robustness(
            base_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH,
            model_directory=ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
            seed_trajectory=ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH,  # noqa: E501
            nseeds=robustness_menu_options.selected_number_of_seeds,
            ensemble=robustness_menu_options.selected_ensemble,
            temperature=robustness_menu_options.selected_temperature,
            timestep=robustness_menu_options.selected_timestep,
            nsteps=robustness_menu_options.selected_number_of_timesteps,
            cap=robustness_menu_options.selected_force_cap or None,
            ncores=robustness_menu_options.selected_number_of_cores,
            executable_path=robustness_menu_options.selected_executable_path or None,
        )
        answer = ""
        user_input_free_flow(
            "DL_FFLUX ROBUSTNESS CHECK SUBMITTED. Press enter to continue: ", answer
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            "DL_FFLUX robustness check job submitted"
        )


# initialize menu
robustness_menu = ConsoleMenu(
    this_menu_options=robustness_menu_options,
    title=ROBUSTNESS_MENU_DESCRIPTION.title,
    subtitle=ROBUSTNESS_MENU_DESCRIPTION.subtitle,
    prologue_text=ROBUSTNESS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=ROBUSTNESS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=ROBUSTNESS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
robustness_menu_items = [
    FunctionItem(
        "Select robustness base path",
        RobustnessMenuFunctions.select_robustness_path,
    ),
    FunctionItem(
        "Select model directory (e.g. a 6_MODEL/xxx subfolder)",
        RobustnessMenuFunctions.select_model_directory_path,
    ),
    FunctionItem(
        "Select seed trajectory (.xyz diversity-sampled set)",
        RobustnessMenuFunctions.select_seed_trajectory_path,
    ),
    FunctionItem(
        "Select number of seed geometries",
        RobustnessMenuFunctions.select_number_of_seeds,
    ),
    FunctionItem(
        "Select ensemble (NVT / NVE)",
        RobustnessMenuFunctions.select_ensemble,
    ),
    FunctionItem(
        "Select simulation temperature",
        RobustnessMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select timestep",
        RobustnessMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select number of timesteps",
        RobustnessMenuFunctions.select_number_of_timesteps,
    ),
    FunctionItem(
        "Select force cap (kT/Angstrom, 0 = disabled)",
        RobustnessMenuFunctions.select_force_cap,
    ),
    FunctionItem(
        "Select number of cores",
        RobustnessMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Select DL_FFLUX executable path (optional override)",
        RobustnessMenuFunctions.select_executable_path,
    ),
    FunctionItem(
        "Set up and submit DL_FFLUX robustness check to compute",
        RobustnessMenuFunctions.submit_robustness_to_compute,
    ),
]

add_items_to_menu(robustness_menu, robustness_menu_items)
