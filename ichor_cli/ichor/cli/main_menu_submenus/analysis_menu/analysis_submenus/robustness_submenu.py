"""The DL_FFLUX robustness menu, which is split into the two halves of a robustness
check: setting up and submitting the runs, and checking the finished runs for broken
bonds. The only thing the two halves share is the base directory holding the runs, which
is why that is the one option living on the top level menu.
"""

import math
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
from ichor.core.files import read_dlpoly_control_settings
from ichor.hpc.molecular_dynamics import (
    submit_dlpoly_fflux_robustness,
    submit_dlpoly_fflux_stability_check,
)

# available DL_POLY ensembles that the menu exposes
ROBUSTNESS_ENSEMBLES = ["nvt", "nve"]

# the per-seed run directories that a robustness check writes into the base path
ROBUSTNESS_RUN_DIRECTORY_GLOB = "RUN*"

# TODO: possibly make this be read from a file
ROBUSTNESS_SETUP_MENU_DEFAULTS = {
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
}

STABILITY_MENU_DEFAULTS = {
    # how often (in timesteps) each trajectory is scanned in the first (cheap) pass. This
    # is only a fallback: the stride is normally derived from the length of the runs, see
    # default_stride_for()
    "default_stride": 1000,
    # a bond counts as exploded when longer than this factor times its reference length
    "default_explosion_factor": 1.35,
    # a bond counts as imploded when shorter than its reference length over this factor
    "default_implosion_factor": 1.50,
    # number of timesteps the runs were meant to last for; 0 = use the longest run
    "default_max_timesteps": 0,
    # length of one timestep (ps), used to convert stabilities into times
    "default_timestep_length": 0.001,
    "default_report_name": "STABILITY-REPORT.txt",
    "default_number_of_cores": 1,
    "default_submit_on_compute": False,
}

ROBUSTNESS_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Robustness Menu",
    subtitle="Use this to run DL_FFLUX simulations from diverse seed geometries "
    "and to check how stable they are (e.g. explosions / implosions).",
)

ROBUSTNESS_SETUP_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Robustness Setup Menu",
    subtitle="Set up and submit one DL_FFLUX simulation per seed geometry.",
)

DL_POLY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "DL_POLY Parameters Menu",
    subtitle="Change the DL_POLY simulation parameters for the robustness check.",
)

STABILITY_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Stability Check Menu",
    subtitle="Check finished DL_FFLUX runs for broken bonds and write a "
    "stability report.",
)


@dataclass
class RobustnessMenuOptions(MenuOptions):
    """Options shared by both halves of a robustness check."""

    # base directory in which the per-seed RUN* directories are created and,
    # afterwards, in which the finished runs are looked for
    selected_dlpoly_robustness_path: Path

    def check_selected_dlpoly_robustness_path(self) -> Union[str, None]:
        """Checks whether the given robustness base path is a directory."""
        base_path = Path(self.selected_dlpoly_robustness_path)
        if base_path.exists() and not base_path.is_dir():
            return f"Current robustness base path: {base_path} is not a directory."


@dataclass
class RobustnessSetupMenuOptions(MenuOptions):
    """Options used when setting up and submitting the runs."""

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


@dataclass
class StabilityCheckMenuOptions(MenuOptions):
    """Options used when checking the finished runs for broken bonds."""

    # reference (usually optimised) geometry defining the intact bond lengths
    selected_reference_geometry_path: Path
    # timesteps between the checks of the first pass over each trajectory, derived from
    # the length of the runs unless the user picks a value
    selected_stride: int
    selected_explosion_factor: float
    selected_implosion_factor: float
    # number of timesteps the runs were meant to last for; 0 = use the longest run
    selected_max_timesteps: int
    # length of one timestep (ps), used to convert stabilities into times
    selected_timestep_length: float
    selected_report_name: str
    selected_submit_on_compute: bool

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


# initialize dataclasses for storing information for the menus
robustness_menu_options = RobustnessMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH,
)

robustness_setup_menu_options = RobustnessSetupMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH,
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_number_of_seeds"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_ensemble"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_temperature"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_timestep"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_number_of_timesteps"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_cutoff"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_force_cap"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_number_of_cores"],
    ROBUSTNESS_SETUP_MENU_DEFAULTS["default_executable_path"],
)

stability_check_menu_options = StabilityCheckMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH,
    STABILITY_MENU_DEFAULTS["default_stride"],
    STABILITY_MENU_DEFAULTS["default_explosion_factor"],
    STABILITY_MENU_DEFAULTS["default_implosion_factor"],
    STABILITY_MENU_DEFAULTS["default_max_timesteps"],
    STABILITY_MENU_DEFAULTS["default_timestep_length"],
    STABILITY_MENU_DEFAULTS["default_report_name"],
    STABILITY_MENU_DEFAULTS["default_submit_on_compute"],
)

# the number of cores is only used when the check is submitted to a compute node, so it is
# asked for as part of submitting rather than taking up a permanent menu option. The last
# answer is remembered as the default for the next time.
stability_check_number_of_cores = STABILITY_MENU_DEFAULTS["default_number_of_cores"]

# the stride is derived from the length of the runs unless the user picks one by hand, in
# which case their choice is kept even when a different set of runs is loaded afterwards
stability_check_stride_overridden = False


def default_stride_for(number_of_timesteps: int) -> int:
    """Returns the stride to check runs of the given length with.

    Checking a run parses roughly ``number_of_timesteps / stride`` geometries in the
    first pass and, if something broke, up to ``stride`` more in the rescan of the window
    the breakage happened in. That total is smallest for a stride of the square root of
    the length of the run, which is what is used here. It also keeps the window in which
    a bond can break and heal again unseen small relative to the run.

    :param number_of_timesteps: The number of timesteps the runs last for. If this is not
        known (0), the menu default is returned instead.
    """

    if number_of_timesteps <= 0:
        return STABILITY_MENU_DEFAULTS["default_stride"]

    return max(1, math.isqrt(number_of_timesteps))


def read_run_settings_from_control(base_path: Path) -> bool:
    """Fills in the stability check settings that the runs themselves already know from
    the CONTROL file of the first run found under the given base path, so that they do
    not have to be typed in again when an existing robustness directory is loaded.

    :param base_path: The robustness base path holding the run directories.
    :return: True if a CONTROL file was read, False if there was none to read (e.g. the
        runs have not been set up yet), in which case the settings are left alone.
    """

    for run_directory in sorted(Path(base_path).glob(ROBUSTNESS_RUN_DIRECTORY_GLOB)):

        control_path = run_directory / "CONTROL"
        if not control_path.is_file():
            continue

        try:
            settings = read_dlpoly_control_settings(control_path)
            # "steps" is the number of timesteps the run was set up to last for, which is
            # what the robustness of the runs is measured against
            stability_check_menu_options.selected_max_timesteps = int(settings["steps"])
            stability_check_menu_options.selected_timestep_length = float(
                settings["timestep"]
            )
            if not stability_check_stride_overridden:
                stability_check_menu_options.selected_stride = default_stride_for(
                    stability_check_menu_options.selected_max_timesteps
                )
        except (OSError, KeyError, ValueError):
            # an unreadable or unexpected CONTROL file is not worth failing over, the
            # settings can still be given by hand
            return False

        return True

    return False


# classes with static methods for each menu item that calls a function.
class RobustnessMenuFunctions:
    """Functions that run when items of the top level robustness menu are selected"""

    @staticmethod
    def select_robustness_path():
        """Select the base directory in which the per-seed RUN* directories are created
        (and in which the finished runs are looked for by the stability check). If the
        directory already holds runs, the number of timesteps and the timestep of the
        stability check are read from the CONTROL file of the first of them."""
        base_path = user_input_path("Enter robustness base path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH = Path(
            base_path
        ).absolute()
        robustness_menu_options.selected_dlpoly_robustness_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH
        )

        if read_run_settings_from_control(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH
        ):
            user_input_free_flow(
                "Read "
                f"{stability_check_menu_options.selected_max_timesteps} timesteps of "
                f"{stability_check_menu_options.selected_timestep_length} ps from the "
                "CONTROL file of the existing runs. Press enter to continue: ",
                "",
            )


class RobustnessSetupMenuFunctions:
    """Functions that run when items of the robustness setup menu are selected"""

    @staticmethod
    def select_model_directory_path():
        """Select the directory containing the trained models (e.g. a 6_MODEL/xxx subfolder)."""
        model_path = user_input_path("Enter model directory path: ")
        ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH = Path(
            model_path
        ).absolute()
        robustness_setup_menu_options.selected_model_directory_path = (
            ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH
        )

    @staticmethod
    def select_seed_trajectory_path():
        """Select the diversity-sampled trajectory (.xyz) that the seeds are taken from."""
        traj_path = user_input_path("Enter seed trajectory .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH = Path(
            traj_path
        ).absolute()
        robustness_setup_menu_options.selected_seed_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH
        )

    @staticmethod
    def select_number_of_seeds():
        """Select how many seed geometries (taken in order) to run."""
        robustness_setup_menu_options.selected_number_of_seeds = user_input_int(
            "Select number of seed geometries: ",
            robustness_setup_menu_options.selected_number_of_seeds,
        )

    @staticmethod
    def select_ensemble():
        """Select the DL_POLY ensemble (NVT or NVE)."""
        robustness_setup_menu_options.selected_ensemble = user_input_restricted(
            ROBUSTNESS_ENSEMBLES,
            "Select ensemble: ",
            robustness_setup_menu_options.selected_ensemble,
        )

    @staticmethod
    def select_temperature():
        """Select the temperature of the simulations."""
        robustness_setup_menu_options.selected_temperature = user_input_int(
            "Select temperature: ", robustness_setup_menu_options.selected_temperature
        )

    @staticmethod
    def select_timestep():
        """Select the timestep (in ps) of the simulations."""
        robustness_setup_menu_options.selected_timestep = user_input_float(
            "Select timestep (ps): ", robustness_setup_menu_options.selected_timestep
        )

    @staticmethod
    def select_number_of_timesteps():
        """Select the number of timesteps of the simulations."""
        robustness_setup_menu_options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps: ",
            robustness_setup_menu_options.selected_number_of_timesteps,
        )

    @staticmethod
    def select_cutoff():
        """Select the real-space cutoff (in Angstrom) for the CONTROL cutoff/rvdw and the
        FFLUX.in electrostatics cut directives. Enter 0 to auto-derive it from the geometry
        (largest interatomic distance + margin), which is a good default for a single molecule
        or small cluster; set an explicit value (e.g. 8-12) for condensed-phase boxes."""
        robustness_setup_menu_options.selected_cutoff = user_input_float(
            "Select real-space cutoff in Angstrom (0 = auto from geometry): ",
            robustness_setup_menu_options.selected_cutoff,
        )

    @staticmethod
    def select_force_cap():
        """Select the force cap (in kT/Angstrom) applied during equilibration. This keeps a
        far-from-equilibrium run (e.g. one using inaccurate FFLUX models) from exploding.
        Enter 0 to disable force capping."""
        robustness_setup_menu_options.selected_force_cap = user_input_float(
            "Select force cap in kT/Angstrom (0 = disabled): ",
            robustness_setup_menu_options.selected_force_cap,
        )

    @staticmethod
    def select_number_of_cores():
        """Select the number of cores to use per run."""
        robustness_setup_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ",
            robustness_setup_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_executable_path():
        """Select an optional DL_FFLUX (DLPOLY.Z) executable path that overrides the
        path configured in ichor_config.yaml. Leave blank to use the configured path."""
        robustness_setup_menu_options.selected_executable_path = user_input_free_flow(
            "Enter DL_FFLUX executable path (blank = use config): ",
            robustness_setup_menu_options.selected_executable_path,
        )

    @staticmethod
    def submit_robustness_to_compute():
        """Sets up one RUN* directory per seed geometry and submits them as a job array."""

        submit_dlpoly_fflux_robustness(
            base_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH,
            model_directory=ichor.cli.global_menu_variables.SELECTED_MODEL_DIRECTORY_PATH,
            seed_trajectory=ichor.cli.global_menu_variables.SELECTED_DLPOLY_SEED_TRAJECTORY_PATH,  # noqa: E501
            nseeds=robustness_setup_menu_options.selected_number_of_seeds,
            ensemble=robustness_setup_menu_options.selected_ensemble,
            temperature=robustness_setup_menu_options.selected_temperature,
            timestep=robustness_setup_menu_options.selected_timestep,
            nsteps=robustness_setup_menu_options.selected_number_of_timesteps,
            cutoff=robustness_setup_menu_options.selected_cutoff or None,
            cap=robustness_setup_menu_options.selected_force_cap or None,
            ncores=robustness_setup_menu_options.selected_number_of_cores,
            executable_path=robustness_setup_menu_options.selected_executable_path
            or None,
        )
        # the runs now exist, so the stability check can take the settings it shares with
        # them (how long they run for) straight from the CONTROL files just written
        read_run_settings_from_control(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_ROBUSTNESS_PATH
        )
        answer = ""
        user_input_free_flow(
            "DL_FFLUX ROBUSTNESS CHECK SUBMITTED. Press enter to continue: ", answer
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            "DL_FFLUX robustness check job submitted"
        )


class StabilityCheckMenuFunctions:
    """Functions that run when items of the stability check menu are selected"""

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
        stability_check_menu_options.selected_reference_geometry_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_REFERENCE_GEOMETRY_PATH
        )

    @staticmethod
    def select_stride():
        """Select how often (in timesteps) each trajectory is checked in the first pass
        of the stability check. A crash is then located exactly by rescanning only the
        (at most one stride long) window in which it must have happened, so a large
        stride makes checking long, stable runs much cheaper.

        The stride is derived from the length of the runs (see :func:`default_stride_for`)
        unless it is given here, in which case the given value is kept for any further
        runs that are loaded. Entering 0 goes back to deriving it."""
        global stability_check_stride_overridden

        stride = user_input_int(
            "Select stability check stride (timesteps, 0 = derive from run length): ",
            stability_check_menu_options.selected_stride,
        )
        derived_stride = default_stride_for(
            stability_check_menu_options.selected_max_timesteps
        )
        # a stride which is (or is asked to be) the derived one is not an override, so
        # loading a different set of runs later is still free to update it
        stability_check_stride_overridden = bool(stride) and stride != derived_stride
        stability_check_menu_options.selected_stride = stride or derived_stride

    @staticmethod
    def select_explosion_factor():
        """Select the factor above which a bond counts as exploded, i.e. a bond is
        broken when it is longer than this factor times its reference bond length."""
        stability_check_menu_options.selected_explosion_factor = user_input_float(
            "Select explosion factor (bond longer than factor * reference): ",
            stability_check_menu_options.selected_explosion_factor,
        )

    @staticmethod
    def select_implosion_factor():
        """Select the factor below which a bond counts as imploded, i.e. a bond is
        broken when it is shorter than its reference bond length divided by this factor."""
        stability_check_menu_options.selected_implosion_factor = user_input_float(
            "Select implosion factor (bond shorter than reference / factor): ",
            stability_check_menu_options.selected_implosion_factor,
        )

    @staticmethod
    def select_max_timesteps():
        """Select the number of timesteps the runs were meant to last for, which is what
        the robustness is measured against (a robustness of 1 means every run survived
        for all of them). Enter 0 to use the longest run in the set instead. This is read
        from the runs' CONTROL file when the base path is selected, so it only has to be
        given by hand for runs that were not set up through this menu."""
        stability_check_menu_options.selected_max_timesteps = user_input_int(
            "Select number of timesteps the runs were set up with (0 = longest run): ",
            stability_check_menu_options.selected_max_timesteps,
        )
        # the stride follows the length of the runs unless it was picked by hand
        if not stability_check_stride_overridden:
            stability_check_menu_options.selected_stride = default_stride_for(
                stability_check_menu_options.selected_max_timesteps
            )

    @staticmethod
    def select_timestep_length():
        """Select the timestep (in ps) the simulations were run with, which is used to
        convert the stability of each run into a time. Like the number of timesteps, this
        is read from the runs' CONTROL file when the base path is selected."""
        stability_check_menu_options.selected_timestep_length = user_input_float(
            "Select timestep (ps) the runs were made with: ",
            stability_check_menu_options.selected_timestep_length,
        )

    @staticmethod
    def select_report_name():
        """Select the name of the stability report file, which is written into the
        robustness base path."""
        stability_check_menu_options.selected_report_name = user_input_free_flow(
            "Enter stability report file name: ",
            stability_check_menu_options.selected_report_name,
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
            Path(base_path) / stability_check_menu_options.selected_report_name
        )
        # 0 means the runs' intended length is unknown, so measure the robustness
        # against the longest run instead
        max_timesteps = stability_check_menu_options.selected_max_timesteps or None

        submit_on_compute = user_input_bool(
            "Submit to compute node (yes/no): ",
            stability_check_menu_options.selected_submit_on_compute,
        )
        stability_check_menu_options.selected_submit_on_compute = submit_on_compute

        if submit_on_compute:

            # only the compute node job needs to know how many cores to ask for
            global stability_check_number_of_cores
            stability_check_number_of_cores = user_input_int(
                "Select number of cores: ", stability_check_number_of_cores
            )

            submit_dlpoly_fflux_stability_check(
                base_path=base_path,
                reference_geometry=reference_geometry,
                report_path=report_path,
                run_directory_glob=ROBUSTNESS_RUN_DIRECTORY_GLOB,
                stride=stability_check_menu_options.selected_stride,
                explosion_factor=stability_check_menu_options.selected_explosion_factor,
                implosion_factor=stability_check_menu_options.selected_implosion_factor,
                max_timesteps=max_timesteps,
                timestep=stability_check_menu_options.selected_timestep_length,
                ncores=stability_check_number_of_cores,
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
                stride=stability_check_menu_options.selected_stride,
                explosion_factor=stability_check_menu_options.selected_explosion_factor,
                implosion_factor=stability_check_menu_options.selected_implosion_factor,
            )
            stability_check.write_report(
                report_path,
                max_timesteps=max_timesteps,
                timestep_length=stability_check_menu_options.selected_timestep_length,
            )

            # show the report as well as writing it, so the runs can be looked over
            # without having to open the file
            print()
            print(
                stability_check.report(
                    max_timesteps=max_timesteps,
                    timestep_length=stability_check_menu_options.selected_timestep_length,
                )
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
                f"STABILITY REPORT WRITTEN TO {report_path}. Press enter to continue: ",
                "",
            )


# initialize menus
# the top level menu only holds the option both halves need (the base path) and the two
# submenus, one per half of a robustness check
robustness_menu = ConsoleMenu(
    this_menu_options=robustness_menu_options,
    title=ROBUSTNESS_MENU_DESCRIPTION.title,
    subtitle=ROBUSTNESS_MENU_DESCRIPTION.subtitle,
    prologue_text=ROBUSTNESS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=ROBUSTNESS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=ROBUSTNESS_MENU_DESCRIPTION.show_exit_option,
)

robustness_setup_menu = ConsoleMenu(
    this_menu_options=robustness_setup_menu_options,
    title=ROBUSTNESS_SETUP_MENU_DESCRIPTION.title,
    subtitle=ROBUSTNESS_SETUP_MENU_DESCRIPTION.subtitle,
    prologue_text=ROBUSTNESS_SETUP_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=ROBUSTNESS_SETUP_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=ROBUSTNESS_SETUP_MENU_DESCRIPTION.show_exit_option,
)

# submenu grouping the DL_POLY simulation parameters, to keep the setup menu short.
# It has no options dataclass of its own (its functions edit the setup menu options,
# which are displayed via the parent setup menu's prologue), so the submit function
# keeps reading the same values.
dl_poly_parameters_menu = ConsoleMenu(
    title=DL_POLY_PARAMETERS_MENU_DESCRIPTION.title,
    subtitle=DL_POLY_PARAMETERS_MENU_DESCRIPTION.subtitle,
    prologue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=DL_POLY_PARAMETERS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=DL_POLY_PARAMETERS_MENU_DESCRIPTION.show_exit_option,
)

stability_check_menu = ConsoleMenu(
    this_menu_options=stability_check_menu_options,
    title=STABILITY_MENU_DESCRIPTION.title,
    subtitle=STABILITY_MENU_DESCRIPTION.subtitle,
    prologue_text=STABILITY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=STABILITY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=STABILITY_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
dl_poly_parameters_menu_items = [
    FunctionItem(
        "Select ensemble (NVT / NVE)",
        RobustnessSetupMenuFunctions.select_ensemble,
    ),
    FunctionItem(
        "Select simulation temperature",
        RobustnessSetupMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select timestep",
        RobustnessSetupMenuFunctions.select_timestep,
    ),
    FunctionItem(
        "Select number of timesteps",
        RobustnessSetupMenuFunctions.select_number_of_timesteps,
    ),
    FunctionItem(
        "Select real-space cutoff (Angstrom, 0 = auto)",
        RobustnessSetupMenuFunctions.select_cutoff,
    ),
    FunctionItem(
        "Select force cap (kT/Angstrom, 0 = disabled)",
        RobustnessSetupMenuFunctions.select_force_cap,
    ),
]
add_items_to_menu(dl_poly_parameters_menu, dl_poly_parameters_menu_items)

robustness_setup_menu_items = [
    FunctionItem(
        "Select model directory (e.g. a 6_MODEL/xxx subfolder)",
        RobustnessSetupMenuFunctions.select_model_directory_path,
    ),
    FunctionItem(
        "Select seed trajectory (.xyz diversity-sampled set)",
        RobustnessSetupMenuFunctions.select_seed_trajectory_path,
    ),
    FunctionItem(
        "Select number of seed geometries",
        RobustnessSetupMenuFunctions.select_number_of_seeds,
    ),
    SubmenuItem(
        "Change DL_POLY parameters (ensemble, temperature, timestep, cutoff, cap)",
        dl_poly_parameters_menu,
        robustness_setup_menu,
    ),
    FunctionItem(
        "Select number of cores",
        RobustnessSetupMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Select DL_FFLUX executable path (optional override)",
        RobustnessSetupMenuFunctions.select_executable_path,
    ),
    FunctionItem(
        "Set up and submit DL_FFLUX robustness check to compute",
        RobustnessSetupMenuFunctions.submit_robustness_to_compute,
    ),
]
add_items_to_menu(robustness_setup_menu, robustness_setup_menu_items)

stability_check_menu_items = [
    FunctionItem(
        "Select reference geometry (.xyz / .gjf, usually the optimised geometry)",
        StabilityCheckMenuFunctions.select_reference_geometry_path,
    ),
    FunctionItem(
        "Override stride (timesteps between checks, 0 = derive from run length)",
        StabilityCheckMenuFunctions.select_stride,
    ),
    FunctionItem(
        "Select explosion factor",
        StabilityCheckMenuFunctions.select_explosion_factor,
    ),
    FunctionItem(
        "Select implosion factor",
        StabilityCheckMenuFunctions.select_implosion_factor,
    ),
    FunctionItem(
        "Override number of timesteps the runs were set up with (0 = longest run)",
        StabilityCheckMenuFunctions.select_max_timesteps,
    ),
    FunctionItem(
        "Override timestep the runs were made with",
        StabilityCheckMenuFunctions.select_timestep_length,
    ),
    FunctionItem(
        "Select stability report file name",
        StabilityCheckMenuFunctions.select_report_name,
    ),
    FunctionItem(
        "Check stability of finished runs (writes stability report)",
        StabilityCheckMenuFunctions.check_stability_of_runs,
    ),
]
add_items_to_menu(stability_check_menu, stability_check_menu_items)

robustness_menu_items = [
    FunctionItem(
        "Select robustness base path",
        RobustnessMenuFunctions.select_robustness_path,
    ),
    SubmenuItem(
        ROBUSTNESS_SETUP_MENU_DESCRIPTION.title,
        robustness_setup_menu,
        robustness_menu,
    ),
    SubmenuItem(
        STABILITY_MENU_DESCRIPTION.title,
        stability_check_menu,
        robustness_menu,
    ),
]

add_items_to_menu(robustness_menu, robustness_menu_items)
