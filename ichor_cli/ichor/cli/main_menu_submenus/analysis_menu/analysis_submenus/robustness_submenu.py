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
    user_input_bool,
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    user_input_restricted,
)
from ichor.core.analysis import DlpolyStabilityCheck
from ichor.hpc.molecular_dynamics import (
    submit_dlpoly_fflux_robustness,
    submit_dlpoly_fflux_stability_check,
)

# available DL_POLY ensembles that the menu exposes
ROBUSTNESS_ENSEMBLES = ["nvt", "nve"]

# the per-seed run directories that a robustness check writes into the base path
ROBUSTNESS_RUN_DIRECTORY_GLOB = "RUN*"

# TODO: possibly make this be read from a file
ROBUSTNESS_MENU_DEFAULTS = {
    "default_number_of_seeds": 10,
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
    # stability check of the finished runs
    # how often (in timesteps) each trajectory is scanned in the first (cheap) pass
    "default_stability_stride": 1000,
    # a bond counts as exploded when longer than this factor times its reference length
    "default_explosion_factor": 1.35,
    # a bond counts as imploded when shorter than its reference length over this factor
    "default_implosion_factor": 1.50,
    "default_stability_report_name": "STABILITY-REPORT.txt",
    "default_submit_stability_on_compute": False,
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
    # real-space cutoff (Angstrom); 0.0 = auto (derived from the geometry)
    selected_cutoff: float
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    selected_force_cap: float
    # computational resources
    selected_number_of_cores: int
    # optional override of the configured DL_FFLUX (DLPOLY.Z) executable path
    selected_executable_path: str
    # stability check of the finished runs
    # reference (usually optimised) geometry defining the intact bond lengths
    selected_reference_geometry_path: Path
    selected_stability_stride: int
    selected_explosion_factor: float
    selected_implosion_factor: float
    selected_stability_report_name: str
    selected_submit_stability_on_compute: bool

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
            return (
                f"Current seed trajectory path: {traj_path} might not be a .xyz file."
            )

    def check_selected_reference_geometry_path(self) -> Union[str, None]:
        """Checks whether the given reference geometry exists and is a .xyz / .gjf file."""
        reference_path = Path(self.selected_reference_geometry_path)
        if not reference_path.exists():
            return f"Current reference geometry path: {reference_path} does not exist."
        elif not reference_path.is_file():
            return f"Current reference geometry path: {reference_path} is not a file."
        elif reference_path.suffix not in [".xyz", ".gjf"]:
            return (
                f"Current reference geometry path: {reference_path} might not be a "
                ".xyz or .gjf file."
            )


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
    ROBUSTNESS_MENU_DEFAULTS["default_cutoff"],
    ROBUSTNESS_MENU_DEFAULTS["default_force_cap"],
    ROBUSTNESS_MENU_DEFAULTS["default_number_of_cores"],
    ROBUSTNESS_MENU_DEFAULTS["default_executable_path"],
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH,
    ROBUSTNESS_MENU_DEFAULTS["default_stability_stride"],
    ROBUSTNESS_MENU_DEFAULTS["default_explosion_factor"],
    ROBUSTNESS_MENU_DEFAULTS["default_implosion_factor"],
    ROBUSTNESS_MENU_DEFAULTS["default_stability_report_name"],
    ROBUSTNESS_MENU_DEFAULTS["default_submit_stability_on_compute"],
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
    def select_cutoff():
        """Select the real-space cutoff (in Angstrom) for the CONTROL cutoff/rvdw and the
        FFLUX.in electrostatics cut directives. Enter 0 to auto-derive it from the geometry
        (largest interatomic distance + margin), which is a good default for a single molecule
        or small cluster; set an explicit value (e.g. 8-12) for condensed-phase boxes."""
        robustness_menu_options.selected_cutoff = user_input_float(
            "Select real-space cutoff in Angstrom (0 = auto from geometry): ",
            robustness_menu_options.selected_cutoff,
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
    def select_reference_geometry_path():
        """Select the reference (usually optimised) geometry whose bond lengths define
        what an intact molecule looks like for the stability check."""
        reference_path = user_input_path(
            "Enter reference geometry (.xyz / .gjf) path: "
        )
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH = Path(
            reference_path
        ).absolute()
        robustness_menu_options.selected_reference_geometry_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH
        )

    @staticmethod
    def select_stability_stride():
        """Select how often (in timesteps) each trajectory is checked in the first pass
        of the stability check. A crash is then located exactly by rescanning only the
        (at most one stride long) window in which it must have happened, so a large
        stride makes checking long, stable runs much cheaper."""
        robustness_menu_options.selected_stability_stride = user_input_int(
            "Select stability check stride (timesteps): ",
            robustness_menu_options.selected_stability_stride,
        )

    @staticmethod
    def select_explosion_factor():
        """Select the factor above which a bond counts as exploded, i.e. a bond is
        broken when it is longer than this factor times its reference bond length."""
        robustness_menu_options.selected_explosion_factor = user_input_float(
            "Select explosion factor (bond longer than factor * reference): ",
            robustness_menu_options.selected_explosion_factor,
        )

    @staticmethod
    def select_implosion_factor():
        """Select the factor below which a bond counts as imploded, i.e. a bond is
        broken when it is shorter than its reference bond length divided by this factor."""
        robustness_menu_options.selected_implosion_factor = user_input_float(
            "Select implosion factor (bond shorter than reference / factor): ",
            robustness_menu_options.selected_implosion_factor,
        )

    @staticmethod
    def select_stability_report_name():
        """Select the name of the stability report file, which is written into the
        robustness base path."""
        robustness_menu_options.selected_stability_report_name = user_input_free_flow(
            "Enter stability report file name: ",
            robustness_menu_options.selected_stability_report_name,
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
            cutoff=robustness_menu_options.selected_cutoff or None,
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

    @staticmethod
    def check_stability_of_runs():
        """Checks the finished runs in the robustness base path for broken bonds
        (explosions / implosions) and writes a stability report containing, for every
        run, the timestep at which it broke (if it did) and which bond went first, as
        well as the overall robustness of the models."""

        base_path = ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH
        reference_geometry = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH
        )
        report_path = (
            Path(base_path) / robustness_menu_options.selected_stability_report_name
        )
        # the runs are meant to last for the number of timesteps they were set up with,
        # which is what the robustness is measured against
        max_timesteps = robustness_menu_options.selected_number_of_timesteps

        submit_on_compute = user_input_bool(
            "Submit to compute node (yes/no): ",
            robustness_menu_options.selected_submit_stability_on_compute,
        )
        robustness_menu_options.selected_submit_stability_on_compute = submit_on_compute

        if submit_on_compute:

            submit_dlpoly_fflux_stability_check(
                base_path=base_path,
                reference_geometry=reference_geometry,
                report_path=report_path,
                run_directory_glob=ROBUSTNESS_RUN_DIRECTORY_GLOB,
                stride=robustness_menu_options.selected_stability_stride,
                explosion_factor=robustness_menu_options.selected_explosion_factor,
                implosion_factor=robustness_menu_options.selected_implosion_factor,
                max_timesteps=max_timesteps,
                timestep=robustness_menu_options.selected_timestep,
                ncores=robustness_menu_options.selected_number_of_cores,
            )
            ichor.hpc.global_variables.LOGGER.info(
                "DL_FFLUX stability check job submitted"
            )
            user_input_free_flow(
                "DL_FFLUX STABILITY CHECK SUBMITTED. Press enter to continue: ", ""
            )

        else:

            run_directories = sorted(
                Path(base_path).glob(ROBUSTNESS_RUN_DIRECTORY_GLOB)
            )
            if not run_directories:
                user_input_free_flow(
                    f"No {ROBUSTNESS_RUN_DIRECTORY_GLOB} directories found in "
                    f"{base_path}. Press enter to continue: ",
                    "",
                )
                return

            print(f"Checking {len(run_directories)} runs, this might take a while...")

            stability_check = DlpolyStabilityCheck(
                reference_geometry,
                run_directories,
                stride=robustness_menu_options.selected_stability_stride,
                explosion_factor=robustness_menu_options.selected_explosion_factor,
                implosion_factor=robustness_menu_options.selected_implosion_factor,
            )
            stability_check.write_report(
                report_path,
                max_timesteps=max_timesteps,
                timestep_length=robustness_menu_options.selected_timestep,
            )

            nstable = sum(1 for r in stability_check.results if not r.crashed)
            robustness = stability_check.robustness(max_timesteps)
            print(
                f"{nstable} / {len(stability_check.results)} runs stayed intact, "
                f"robustness: {robustness:.4f}"
            )
            ichor.hpc.global_variables.LOGGER.info(
                f"DL_FFLUX stability check written to {report_path}, "
                f"robustness: {robustness:.4f}"
            )
            user_input_free_flow(
                f"STABILITY REPORT WRITTEN TO {report_path}. "
                "Press enter to continue: ",
                "",
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

# submenu grouping the DL_POLY simulation parameters, to keep the main robustness menu short.
# It has no options dataclass of its own (its functions edit the shared robustness_menu_options,
# which is displayed via the parent robustness menu's prologue), so the submit function keeps
# reading the same values.
DL_POLY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "DL_POLY Parameters Menu",
    subtitle="Change the DL_POLY simulation parameters for the robustness check.",
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
        "Select real-space cutoff (Angstrom, 0 = auto)",
        RobustnessMenuFunctions.select_cutoff,
    ),
    FunctionItem(
        "Select force cap (kT/Angstrom, 0 = disabled)",
        RobustnessMenuFunctions.select_force_cap,
    ),
]
add_items_to_menu(dl_poly_parameters_menu, dl_poly_parameters_menu_items)

# submenu grouping the parameters of the stability check of the finished runs. Like the
# DL_POLY parameters menu it has no options dataclass of its own, its functions edit the
# shared robustness_menu_options.
STABILITY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "Stability Check Parameters Menu",
    subtitle="Change the parameters of the stability check of the finished runs.",
)
stability_parameters_menu = ConsoleMenu(
    title=STABILITY_PARAMETERS_MENU_DESCRIPTION.title,
    subtitle=STABILITY_PARAMETERS_MENU_DESCRIPTION.subtitle,
    prologue_text=STABILITY_PARAMETERS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=STABILITY_PARAMETERS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=STABILITY_PARAMETERS_MENU_DESCRIPTION.show_exit_option,
)
stability_parameters_menu_items = [
    FunctionItem(
        "Select stride (timesteps between checks)",
        RobustnessMenuFunctions.select_stability_stride,
    ),
    FunctionItem(
        "Select explosion factor",
        RobustnessMenuFunctions.select_explosion_factor,
    ),
    FunctionItem(
        "Select implosion factor",
        RobustnessMenuFunctions.select_implosion_factor,
    ),
    FunctionItem(
        "Select stability report file name",
        RobustnessMenuFunctions.select_stability_report_name,
    ),
]
add_items_to_menu(stability_parameters_menu, stability_parameters_menu_items)

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
    SubmenuItem(
        "Change DL_POLY parameters (ensemble, temperature, timestep, cutoff, cap)",
        dl_poly_parameters_menu,
        robustness_menu,
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
    FunctionItem(
        "Select reference geometry for stability check (.xyz / .gjf)",
        RobustnessMenuFunctions.select_reference_geometry_path,
    ),
    SubmenuItem(
        "Change stability check parameters (stride, explosion / implosion factors)",
        stability_parameters_menu,
        robustness_menu,
    ),
    FunctionItem(
        "Check stability of finished runs (writes stability report)",
        RobustnessMenuFunctions.check_stability_of_runs,
    ),
]

add_items_to_menu(robustness_menu, robustness_menu_items)
