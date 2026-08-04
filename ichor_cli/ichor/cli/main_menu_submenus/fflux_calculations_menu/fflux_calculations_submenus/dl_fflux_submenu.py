from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
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
from ichor.hpc.molecular_dynamics import submit_dlpoly_fflux

# available DL_POLY ensembles that the menu exposes
DL_FFLUX_ENSEMBLES = ["nvt", "nve"]

# TODO: possibly make this be read from a file
DL_FFLUX_MENU_DEFAULTS = {
    "default_ensemble": "nvt",
    "default_temperature": 300,
    "default_timestep": 0.001,
    "default_number_of_timesteps": 500,
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    "default_cutoff": 0.0,
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    "default_force_cap": 0.0,
    "default_number_of_cores": 1,
    # empty string means "use the executable path from the config"
    "default_executable_path": "",
}

DL_FFLUX_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Menu",
    subtitle="Use this to set up and submit a DL_FFLUX (FFLUX-based DL_POLY) calculation.",
)

# TODO: Check about dimer calculations - how to support this?


@dataclass
class DLFFLUXMenuOptions(MenuOptions):
    # location where the DL_FFLUX calculation is set up and run
    selected_dlpoly_run_path: Path
    # location of the trained models (usually one of the 6_MODEL/xxx subfolders)
    selected_model_directory_path: Path
    # starting geometry (.xyz) written to the CONFIG file
    selected_xyz_path: Path
    # DL_POLY calculation parameters
    selected_ensemble: str
    selected_temperature: int
    selected_timestep: float
    selected_number_of_timesteps: int
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    selected_cutoff: float
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

    def check_selected_xyz_path(self) -> Union[str, None]:
        """Checks whether the given starting geometry exists and is a .xyz file."""
        xyz_path = Path(self.selected_xyz_path)
        if not xyz_path.exists():
            return f"Current starting geometry path: {xyz_path} does not exist."
        elif not xyz_path.is_file():
            return f"Current starting geometry path: {xyz_path} is not a file."
        elif xyz_path.suffix != ".xyz":
            return (
                f"Current starting geometry path: {xyz_path} might not be a .xyz file."
            )


# initialize dataclass for storing information for menu
dl_fflux_menu_options = DLFFLUXMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH,
    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
    ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
    DL_FFLUX_MENU_DEFAULTS["default_ensemble"],
    DL_FFLUX_MENU_DEFAULTS["default_temperature"],
    DL_FFLUX_MENU_DEFAULTS["default_timestep"],
    DL_FFLUX_MENU_DEFAULTS["default_number_of_timesteps"],
    DL_FFLUX_MENU_DEFAULTS["default_cutoff"],
    DL_FFLUX_MENU_DEFAULTS["default_force_cap"],
    DL_FFLUX_MENU_DEFAULTS["default_number_of_cores"],
    DL_FFLUX_MENU_DEFAULTS["default_executable_path"],
)


# class with static methods for each menu item that calls a function.
class DLFFLUXMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_dlpoly_run_path():
        """Select the directory in which the DL_FFLUX calculation is set up and run."""
        run_path = user_input_path("Enter DL_FFLUX run path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH = Path(
            run_path
        ).absolute()
        dl_fflux_menu_options.selected_dlpoly_run_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH
        )

    @staticmethod
    def select_model_directory_path():
        """Select the directory containing the trained models (e.g. a 6_MODEL/xxx subfolder)."""
        model_path = user_input_path("Enter model directory path: ")
        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH = Path(
            model_path
        ).absolute()
        dl_fflux_menu_options.selected_model_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
        )

    @staticmethod
    def select_xyz():
        """Select the .xyz file containing the starting geometry."""
        xyz_path = user_input_path("Enter starting geometry .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        dl_fflux_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )

    @staticmethod
    def select_ensemble():
        """Select the DL_POLY ensemble (NVT or NVE)."""
        dl_fflux_menu_options.selected_ensemble = user_input_restricted(
            DL_FFLUX_ENSEMBLES,
            "Select ensemble: ",
            dl_fflux_menu_options.selected_ensemble,
        )

    @staticmethod
    def select_temperature():
        """Select the temperature of the DL_FFLUX simulation."""
        dl_fflux_menu_options.selected_temperature = user_input_int(
            "Select temperature: ", dl_fflux_menu_options.selected_temperature
        )

    @staticmethod
    def select_timestep():
        """Select the timestep (in ps) of the DL_FFLUX simulation."""
        dl_fflux_menu_options.selected_timestep = user_input_float(
            "Select timestep (ps): ", dl_fflux_menu_options.selected_timestep
        )

    @staticmethod
    def select_number_of_timesteps():
        """Select the number of timesteps of the DL_FFLUX simulation."""
        dl_fflux_menu_options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps: ",
            dl_fflux_menu_options.selected_number_of_timesteps,
        )

    @staticmethod
    def select_cutoff():
        """Select the real-space cutoff (in Angstrom) for the CONTROL cutoff/rvdw and the
        FFLUX.in electrostatics cut directives. Enter 0 to auto-derive it from the geometry
        (largest interatomic distance + margin), which is a good default for a single molecule
        or small cluster; set an explicit value (e.g. 8-12) for condensed-phase boxes."""
        dl_fflux_menu_options.selected_cutoff = user_input_float(
            "Select real-space cutoff in Angstrom (0 = auto from geometry): ",
            dl_fflux_menu_options.selected_cutoff,
        )

    @staticmethod
    def select_force_cap():
        """Select the force cap (in kT/Angstrom) applied during equilibration. This keeps a
        far-from-equilibrium run (e.g. one using inaccurate FFLUX models) from exploding.
        Enter 0 to disable force capping."""
        dl_fflux_menu_options.selected_force_cap = user_input_float(
            "Select force cap in kT/Angstrom (0 = disabled): ",
            dl_fflux_menu_options.selected_force_cap,
        )

    @staticmethod
    def select_number_of_cores():
        """Select the number of cores to use for the DL_FFLUX job."""
        dl_fflux_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ",
            dl_fflux_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_executable_path():
        """Select an optional DL_FFLUX (DLPOLY.Z) executable path that overrides the
        path configured in ichor_config.yaml. Leave blank to use the configured path."""
        dl_fflux_menu_options.selected_executable_path = user_input_free_flow(
            "Enter DL_FFLUX executable path (blank = use config): ",
            dl_fflux_menu_options.selected_executable_path,
        )

    @staticmethod
    def submit_dl_fflux_to_compute():
        """Sets up the DL_FFLUX directory and submits the job to a compute node."""

        submit_dlpoly_fflux(
            run_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH,
            model_directory=ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
            starting_geometry=ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            ensemble=dl_fflux_menu_options.selected_ensemble,
            temperature=dl_fflux_menu_options.selected_temperature,
            timestep=dl_fflux_menu_options.selected_timestep,
            nsteps=dl_fflux_menu_options.selected_number_of_timesteps,
            cutoff=dl_fflux_menu_options.selected_cutoff or None,
            cap=dl_fflux_menu_options.selected_force_cap or None,
            ncores=dl_fflux_menu_options.selected_number_of_cores,
            executable_path=dl_fflux_menu_options.selected_executable_path or None,
        )
        answer = ""
        user_input_free_flow("DL_FFLUX SUBMITTED. Press enter to continue: ", answer)
        # update logger
        ichor.hpc.global_variables.LOGGER.info("DL_FFLUX job submitted")


# initialize menu
dl_fflux_menu = ConsoleMenu(
    this_menu_options=dl_fflux_menu_options,
    title=DL_FFLUX_MENU_DESCRIPTION.title,
    subtitle=DL_FFLUX_MENU_DESCRIPTION.subtitle,
    prologue_text=DL_FFLUX_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=DL_FFLUX_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=DL_FFLUX_MENU_DESCRIPTION.show_exit_option,
)

# submenu grouping the DL_POLY simulation parameters, to keep the main DL_FFLUX menu short.
# It has no options dataclass of its own (its functions edit the shared dl_fflux_menu_options,
# which is displayed via the parent DL_FFLUX menu's prologue), so the submit function keeps
# reading the same values.
DL_POLY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "DL_POLY Parameters Menu",
    subtitle="Change the DL_POLY simulation parameters for the DL_FFLUX calculation.",
)
dl_poly_parameters_menu = ConsoleMenu(
    title=DL_POLY_PARAMETERS_MENU_DESCRIPTION.title,
    subtitle=DL_POLY_PARAMETERS_MENU_DESCRIPTION.subtitle,
    prologue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=DL_POLY_PARAMETERS_MENU_DESCRIPTION.show_exit_option,
)
dl_poly_parameters_menu_items = [
    FunctionItem(
        "Select ensemble (NVT / NVE)",
        DLFFLUXMenuFunctions.select_ensemble,
    ),
    FunctionItem(
        "Select simulation temperature",
        DLFFLUXMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select timestep",
        DLFFLUXMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select number of timesteps",
        DLFFLUXMenuFunctions.select_number_of_timesteps,
    ),
    FunctionItem(
        "Select real-space cutoff (Angstrom, 0 = auto)",
        DLFFLUXMenuFunctions.select_cutoff,
    ),
    FunctionItem(
        "Select force cap (kT/Angstrom, 0 = disabled)",
        DLFFLUXMenuFunctions.select_force_cap,
    ),
]
add_items_to_menu(dl_poly_parameters_menu, dl_poly_parameters_menu_items)

# make menu items
# can use lambda functions to change text of options as well :)
dl_fflux_menu_items = [
    FunctionItem(
        "Select DL_FFLUX run path",
        DLFFLUXMenuFunctions.select_dlpoly_run_path,
    ),
    FunctionItem(
        "Select model directory (e.g. a 6_MODEL/xxx subfolder)",
        DLFFLUXMenuFunctions.select_model_directory_path,
    ),
    FunctionItem(
        "Select starting geometry (.xyz)",
        DLFFLUXMenuFunctions.select_xyz,
    ),
    SubmenuItem(
        "Change DL_POLY parameters (ensemble, temperature, timestep, cutoff, cap)",
        dl_poly_parameters_menu,
        dl_fflux_menu,
    ),
    FunctionItem(
        "Select number of cores",
        DLFFLUXMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Select DL_FFLUX executable path (optional override)",
        DLFFLUXMenuFunctions.select_executable_path,
    ),
    FunctionItem(
        "Set up and submit DL_FFLUX job to compute",
        DLFFLUXMenuFunctions.submit_dl_fflux_to_compute,
    ),
]

add_items_to_menu(dl_fflux_menu, dl_fflux_menu_items)
