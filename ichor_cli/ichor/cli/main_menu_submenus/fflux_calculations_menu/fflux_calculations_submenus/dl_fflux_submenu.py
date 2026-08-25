from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.fflux_calculations_menu.fflux_calculations_submenus.dl_fflux_parameters import (  # noqa: E501
    DL_POLY_PARAMETER_DEFAULTS,
    make_dl_poly_parameters_menu,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    directory_selected,
    print_summary_and_pause,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    xyz_file_selected,
)
from ichor.hpc.molecular_dynamics import submit_dlpoly_fflux

# what entering 0 for the real-space cutoff does here: a single molecule sits in a box whose
# size is arbitrary, so the cutoff is sized to hold the molecule and the box grown around it
CUTOFF_HELP = "auto from geometry"

# TODO: possibly make this be read from a file
DL_FFLUX_MENU_DEFAULTS = {
    **DL_POLY_PARAMETER_DEFAULTS,
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
    # base directory the DL_FFLUX calculation is set up under; each submitted calculation
    # gets its own RUN<i> directory inside it, all sharing one copy of the models
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
        """Select the base directory the DL_FFLUX calculation is set up under. The
        calculation is set up in its own RUN<i> directory inside it (RUN0 for the first,
        RUN1 for the next, ...), all of which share the one copy of the models kept in the
        base directory, so submitting several calculations with the same path here adds a
        run instead of overwriting the previous one."""
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
        """Sets up a RUN<i> directory under the DL_FFLUX run path and submits the job to a
        compute node."""

        # all three paths default to the directory ichor is running in, so without these
        # a run is set up next to wherever ichor was started, with no models to run on
        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH,
            "submit the DL_FFLUX job",
            what="run path",
            # the run path is made if it is not there, so only the choice of it matters
            must_exist=False,
            select_with="Use 'Select DL_FFLUX run path' in this menu first.",
        ):
            return

        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
            "submit the DL_FFLUX job",
            what="model directory",
            select_with="Use 'Select model directory' in this menu to select the "
            "folder of trained models (usually one of the 6_MODELS subfolders).",
        ):
            return

        if not xyz_file_selected(
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
            "submit the DL_FFLUX job",
            what="starting geometry",
            select_with="Use 'Select starting geometry (.xyz)' in this menu first.",
        ):
            return

        try:
            job_id = submit_dlpoly_fflux(
                base_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH,
                model_directory=ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,  # noqa: E501
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
        except ValueError as error:
            # e.g. the run path already holds runs sharing a different set of models,
            # which is worth saying rather than crashing out of the menu with a traceback
            ichor.hpc.global_variables.LOGGER.error(
                f"DL_FFLUX job not submitted: {error}"
            )
            print_summary_and_pause(
                "DL_FFLUX JOB NOT SUBMITTED",
                {
                    "Run path": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH
                    ),
                    "Model directory": (
                        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
                    ),
                    "Reason": error,
                },
                [
                    "Every run under one run path shares the single copy of the models "
                    "kept there, so a run path can only be reused with the models it "
                    "already holds. Pick an empty (or new) run path to use a different "
                    "set of models.",
                ],
            )
            return

        nsteps = dl_fflux_menu_options.selected_number_of_timesteps
        timestep = dl_fflux_menu_options.selected_timestep
        cutoff = dl_fflux_menu_options.selected_cutoff
        force_cap = dl_fflux_menu_options.selected_force_cap

        print_summary_and_pause(
            "DL_FFLUX JOB SUBMITTED",
            {
                "Run path": ichor.cli.global_menu_variables.SELECTED_DLPOLY_RUN_PATH,
                "Model directory": (
                    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
                ),
                "Starting geometry": ichor.cli.global_menu_variables.SELECTED_XYZ_PATH,
                "Job ID": job_id.id if job_id else "not available",
                "Ensemble": dl_fflux_menu_options.selected_ensemble.upper(),
                "Temperature": f"{dl_fflux_menu_options.selected_temperature} K",
                "Timestep": f"{timestep} ps",
                "Timesteps": f"{nsteps:,}",
                "Simulated time": f"{nsteps * timestep:,.3f} ps",
                "Cutoff": (
                    f"{cutoff} Angstrom" if cutoff else "auto (from the geometry)"
                ),
                "Force cap": (f"{force_cap} kT/Angstrom" if force_cap else "disabled"),
                "CPU cores": dl_fflux_menu_options.selected_number_of_cores,
                "Executable": (
                    dl_fflux_menu_options.selected_executable_path or "from config"
                ),
            },
            [
                "The calculation has been set up in its own RUN<i> directory under the "
                "run path, next to the shared copy of the models; submitting again "
                "with the same run path adds another run rather than overwriting this "
                "one.",
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue).",
                "DL_FFLUX writes its trajectory (HISTORY) and energies (STATIS) into "
                "the run directory; the analysis menu's stability check reads those to "
                "tell you whether the run stayed intact.",
            ],
        )
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
# It edits this menu's own options (which the parent DL_FFLUX menu's prologue displays), so
# the submit function keeps reading the same values.
dl_poly_parameters_menu = make_dl_poly_parameters_menu(
    dl_fflux_menu_options, CUTOFF_HELP
)

# make menu items
# can use lambda functions to change text of options as well :)
dl_fflux_menu_items = [
    FunctionItem(
        "Select DL_FFLUX run path (RUN0, RUN1, ... are made within)",
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
        "Change DL_POLY parameters",
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
