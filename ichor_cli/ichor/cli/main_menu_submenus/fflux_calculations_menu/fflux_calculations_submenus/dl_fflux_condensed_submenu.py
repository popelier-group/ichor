from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Union

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
    directories_selected,
    directory_selected,
    print_summary_and_pause,
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_path,
    xyz_file_selected,
)
from ichor.hpc.molecular_dynamics import (
    dlpoly_fflux_composition,
    submit_dlpoly_fflux_condensed,
)

# what entering 0 for the real-space cutoff does here: the box is a fixed size (it is what
# sets the density), so the cutoff is fitted to it rather than the other way around
CUTOFF_HELP = "auto from box"

# TODO: possibly make this be read from a file
DL_FFLUX_CONDENSED_MENU_DEFAULTS = {
    **DL_POLY_PARAMETER_DEFAULTS,
    # the width (Angstrom) of the cubic box the geometry was packed into. 0.0 means it has
    # not been given yet, which a condensed phase run cannot be set up without.
    "default_cell_size": 0.0,
    "default_number_of_cores": 1,
    # empty string means "use the executable path from the config"
    "default_executable_path": "",
}

DL_FFLUX_CONDENSED_MENU_DESCRIPTION = MenuDescription(
    "DL_FFLUX Condensed Phase Menu",
    subtitle="Use this to set up and submit a DL_FFLUX simulation of a periodic box of molecules.",  # noqa: E501
)


@dataclass
class DLFFLUXCondensedMenuOptions(MenuOptions):
    # base directory the DL_FFLUX calculation is set up under; each submitted calculation
    # gets its own RUN<i> directory inside it, all sharing one copy of the models
    selected_dlpoly_run_path: Path
    # starting geometry (.xyz): the packed box, e.g. as written by Packmol
    selected_xyz_path: Path
    # width (Angstrom) of the cubic box the geometry was packed into
    selected_cell_size: float
    # locations of the trained models, one per molecular species in the box (usually
    # 6_MODEL/xxx subfolders). Which set belongs to which species is worked out from the
    # atoms the models were made for, so the order they are added in does not matter.
    selected_model_directory_paths: List[Path] = field(default_factory=list)
    # DL_POLY calculation parameters
    selected_ensemble: str = DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_ensemble"]
    selected_temperature: int = DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_temperature"]
    selected_timestep: float = DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_timestep"]
    selected_number_of_timesteps: int = DL_FFLUX_CONDENSED_MENU_DEFAULTS[
        "default_number_of_timesteps"
    ]
    # real-space cutoff (Angstrom); 0.0 = auto (fitted to the box)
    selected_cutoff: float = DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_cutoff"]
    # force cap (kT/Angstrom) applied during equilibration; 0.0 disables it
    selected_force_cap: float = DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_force_cap"]
    # computational resources
    selected_number_of_cores: int = DL_FFLUX_CONDENSED_MENU_DEFAULTS[
        "default_number_of_cores"
    ]
    # optional override of the configured DL_FFLUX (DLPOLY.Z) executable path
    selected_executable_path: str = DL_FFLUX_CONDENSED_MENU_DEFAULTS[
        "default_executable_path"
    ]

    def get_display_value(self, value):
        """Displays the list of model directories as its shortened paths, rather than as a
        raw list of ``PosixPath(...)`` reprs."""
        if isinstance(value, list):
            if not value:
                return "none selected"
            # MenuOptions rather than super(), which does not work inside a comprehension
            return ", ".join(
                str(MenuOptions.get_display_value(self, item)) for item in value
            )
        return super().get_display_value(value)

    def check_selected_model_directory_paths(self) -> Union[str, None]:
        """Checks that model directories have been given and that they exist."""
        if not self.selected_model_directory_paths:
            return "No model directory has been selected."
        for model_path in self.selected_model_directory_paths:
            model_path = Path(model_path)
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

    def check_selected_cell_size(self) -> Union[str, None]:
        """Checks that the size of the packed box has been given. Unlike a single molecule
        run there is no sensible default for it: it is what sets the density of the
        simulation, so it has to be the box the geometry was actually packed into."""
        if not self.selected_cell_size or self.selected_cell_size <= 0:
            return (
                "No box size has been selected. Enter the width of the box the geometry "
                "was packed into."
            )


# initialize dataclass for storing information for menu
dl_fflux_condensed_menu_options = DLFFLUXCondensedMenuOptions(
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH,
    ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH,
    DL_FFLUX_CONDENSED_MENU_DEFAULTS["default_cell_size"],
    list(ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS),
)


def box_and_models_selected(action: str) -> bool:
    """Checks that the packed box and the models to run it with have been selected, as
    both the composition of the box and the calculation itself are worked out from them.

    :param action: What the option would do with them, e.g. ``"submit the DL_FFLUX job"``.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    if not xyz_file_selected(
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH,
        action,
        what="packed box",
        select_with="Use 'Select packed box (.xyz)' in this menu first.",
    ):
        return False

    return directories_selected(
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS,
        action,
        what="model directory",
        select_with="Use 'Add model directory' in this menu to add one folder of "
        "trained models per kind of molecule in the box.",
    )


# class with static methods for each menu item that calls a function.
class DLFFLUXCondensedMenuFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_dlpoly_run_path():
        """Select the base directory the DL_FFLUX calculation is set up under. The
        calculation is set up in its own RUN<i> directory inside it (RUN0 for the first,
        RUN1 for the next, ...), all of which share the one copy of the models kept in the
        base directory, so submitting several calculations with the same path here adds a
        run instead of overwriting the previous one."""
        run_path = user_input_path("Enter DL_FFLUX run path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH = Path(
            run_path
        ).absolute()
        dl_fflux_condensed_menu_options.selected_dlpoly_run_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH
        )

    @staticmethod
    def add_model_directory_path():
        """Add a directory of trained models (e.g. a 6_MODEL/xxx subfolder) to the ones the
        simulation uses. A box of a single substance needs one; a mixture needs one per
        molecular species in it, added one at a time. Which set of models belongs to which
        species is worked out from the atoms they were made for, so they can be added in
        any order."""
        model_path = user_input_path("Enter model directory path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS.append(
            Path(model_path).absolute()
        )
        dl_fflux_condensed_menu_options.selected_model_directory_paths = list(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS
        )

    @staticmethod
    def clear_model_directory_paths():
        """Forget the model directories selected so far, to start choosing them again."""
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS.clear()
        dl_fflux_condensed_menu_options.selected_model_directory_paths = []

    @staticmethod
    def select_xyz():
        """Select the .xyz file holding the packed box (e.g. as written by Packmol). What
        the box is made of does not have to be stated - it is worked out from the geometry
        itself."""
        xyz_path = user_input_path("Enter packed box .xyz path: ")
        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH = Path(
            xyz_path
        ).absolute()
        dl_fflux_condensed_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH
        )

    @staticmethod
    def select_cell_size():
        """Select the width (in Angstrom) of the cubic box the geometry was packed into.
        This is the box size Packmol (or whatever packed the geometry) was given: it sets
        the density of the simulation, so it must match the geometry rather than be chosen
        freely."""
        dl_fflux_condensed_menu_options.selected_cell_size = user_input_float(
            "Select box size in Angstrom: ",
            dl_fflux_condensed_menu_options.selected_cell_size,
        )

    @staticmethod
    def select_number_of_cores():
        """Select the number of cores to use for the DL_FFLUX job."""
        dl_fflux_condensed_menu_options.selected_number_of_cores = user_input_int(
            "Select number of cores: ",
            dl_fflux_condensed_menu_options.selected_number_of_cores,
        )

    @staticmethod
    def select_executable_path():
        """Select an optional DL_FFLUX (DLPOLY.Z) executable path that overrides the
        path configured in the ichor config file. Leave blank to use the configured path."""
        dl_fflux_condensed_menu_options.selected_executable_path = user_input_free_flow(
            "Enter DL_FFLUX executable path (blank = use config): ",
            dl_fflux_condensed_menu_options.selected_executable_path,
        )

    @staticmethod
    def show_composition():
        """Work out what the selected box is made of, without setting anything up or
        submitting anything. This is worth a look before submitting, because nothing states
        the composition of the box - it is read off the geometry, so this is the chance to
        check that what ichor found is what was packed."""

        if not box_and_models_selected("work out what the box is made of"):
            return

        try:
            composition = dlpoly_fflux_composition(
                ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH,
                ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS,
            )
        except (ValueError, OSError) as error:
            print_summary_and_pause(
                "COULD NOT WORK OUT WHAT THE BOX IS MADE OF",
                {
                    "Packed box": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH  # noqa: E501
                    ),
                    "Reason": error,
                },
                [
                    "The box is split into molecules along its bonds and each kind of "
                    "molecule is matched to the models made for it, so this needs one "
                    "model directory per kind of molecule in the box.",
                ],
            )
            return

        print_summary_and_pause(
            "WHAT THE BOX IS MADE OF",
            {
                "Packed box": (
                    ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH
                ),
                "Molecules": f"{composition.nmolecules:,}",
                "Atoms": f"{composition.total_atoms:,}",
                "Composition": str(composition),
            },
            [
                "Each species is named after the models it was matched to, which is the "
                "name its atoms are labelled with in the CONFIG file so that DL_FFLUX "
                "finds their models.",
            ],
        )

    @staticmethod
    def submit_dl_fflux_to_compute():
        """Sets up a RUN<i> directory under the DL_FFLUX run path and submits the job to a
        compute node."""

        options = dl_fflux_condensed_menu_options

        # every path defaults to the directory ichor is running in, so without these a
        # run is set up next to wherever ichor was started, with no models to run on
        if not directory_selected(
            ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH,
            "submit the DL_FFLUX job",
            what="run path",
            # the run path is made if it is not there, so only the choice of it matters
            must_exist=False,
            select_with="Use 'Select DL_FFLUX run path' in this menu first.",
        ):
            return

        if not box_and_models_selected("submit the DL_FFLUX job"):
            return

        # unlike a single molecule run, there is no sensible default for the size of the
        # box: it is what sets the density of the simulation
        if options.selected_cell_size <= 0:
            print_summary_and_pause(
                "CANNOT SUBMIT THE DL_FFLUX JOB",
                {
                    "Packed box": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH  # noqa: E501
                    ),
                    "Problem": "No box size has been selected.",
                },
                [
                    "Nothing has been done, as the size of the box the geometry was "
                    "packed into is what sets the density of the simulation, and it "
                    "cannot be guessed from the geometry.",
                    "Use 'Select box size (Angstrom)' in this menu to give the box size "
                    "that Packmol (or whatever packed the geometry) was given.",
                ],
            )
            return

        try:
            job_id, composition = submit_dlpoly_fflux_condensed(
                base_path=ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH,  # noqa: E501
                model_directory=ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_MODEL_PATHS,  # noqa: E501
                starting_geometry=ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH,  # noqa: E501
                cell_size=options.selected_cell_size,
                ensemble=options.selected_ensemble,
                temperature=options.selected_temperature,
                timestep=options.selected_timestep,
                nsteps=options.selected_number_of_timesteps,
                cutoff=options.selected_cutoff or None,
                cap=options.selected_force_cap or None,
                ncores=options.selected_number_of_cores,
                executable_path=options.selected_executable_path or None,
            )
        except ValueError as error:
            # e.g. the models cannot be matched to what is in the box, the box is too small
            # for its own molecules, or the run path already holds runs sharing a different
            # set of models - all worth saying rather than crashing out of the menu with a
            # traceback
            ichor.hpc.global_variables.LOGGER.error(
                f"Condensed phase DL_FFLUX job not submitted: {error}"
            )
            print_summary_and_pause(
                "DL_FFLUX JOB NOT SUBMITTED",
                {
                    "Run path": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH  # noqa: E501
                    ),
                    "Packed box": (
                        ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH  # noqa: E501
                    ),
                    "Box size": f"{options.selected_cell_size} Angstrom",
                    "Reason": error,
                },
                [
                    "A condensed phase run needs one model directory per kind of molecule "
                    "in the box, and a box size which is the one the geometry was packed "
                    "into.",
                    "Every run under one run path shares the single copy of the models "
                    "kept there, so a run path can only be reused with the models it "
                    "already holds. Pick an empty (or new) run path to use a different "
                    "set of models.",
                ],
            )
            return

        nsteps = options.selected_number_of_timesteps
        timestep = options.selected_timestep
        cutoff = options.selected_cutoff
        force_cap = options.selected_force_cap

        print_summary_and_pause(
            "DL_FFLUX JOB SUBMITTED",
            {
                "Run path": (
                    ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_RUN_PATH
                ),
                "Packed box": (
                    ichor.cli.global_menu_variables.SELECTED_DLPOLY_CONDENSED_XYZ_PATH
                ),
                "Composition": str(composition),
                "Molecules": f"{composition.nmolecules:,}",
                "Atoms": f"{composition.total_atoms:,}",
                "Box size": f"{options.selected_cell_size} Angstrom",
                "Job ID": job_id.id if job_id else "not available",
                "Ensemble": options.selected_ensemble.upper(),
                "Temperature": f"{options.selected_temperature} K",
                "Timestep": f"{timestep} ps",
                "Timesteps": f"{nsteps:,}",
                "Simulated time": f"{nsteps * timestep:,.3f} ps",
                "Cutoff": (f"{cutoff} Angstrom" if cutoff else "auto (from the box)"),
                "Force cap": (f"{force_cap} kT/Angstrom" if force_cap else "disabled"),
                "CPU cores": options.selected_number_of_cores,
                "Executable": (options.selected_executable_path or "from config"),
            },
            [
                "What the box is made of was read off the geometry rather than stated, so "
                "it is worth checking the composition above is what was packed.",
                "The calculation has been set up in its own RUN<i> directory under the "
                "run path, next to the shared copy of the models; submitting again "
                "with the same run path adds another run rather than overwriting this "
                "one.",
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue).",
                "DL_FFLUX writes its trajectory (HISTORY) and energies (STATIS) into "
                "the run directory.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info("Condensed phase DL_FFLUX job submitted")


# initialize menu
dl_fflux_condensed_menu = ConsoleMenu(
    this_menu_options=dl_fflux_condensed_menu_options,
    title=DL_FFLUX_CONDENSED_MENU_DESCRIPTION.title,
    subtitle=DL_FFLUX_CONDENSED_MENU_DESCRIPTION.subtitle,
    prologue_text=DL_FFLUX_CONDENSED_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=DL_FFLUX_CONDENSED_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=DL_FFLUX_CONDENSED_MENU_DESCRIPTION.show_exit_option,
)

# submenu grouping the DL_POLY simulation parameters, to keep the main menu short. It edits
# this menu's own options (which this menu's prologue displays), so the submit function
# keeps reading the same values.
dl_poly_parameters_menu = make_dl_poly_parameters_menu(
    dl_fflux_condensed_menu_options, CUTOFF_HELP
)

# make menu items
dl_fflux_condensed_menu_items = [
    FunctionItem(
        "Select DL_FFLUX run path (RUN0, RUN1, ... are made within)",
        DLFFLUXCondensedMenuFunctions.select_dlpoly_run_path,
    ),
    FunctionItem(
        "Select packed box (.xyz)",
        DLFFLUXCondensedMenuFunctions.select_xyz,
    ),
    FunctionItem(
        "Select box size (Angstrom)",
        DLFFLUXCondensedMenuFunctions.select_cell_size,
    ),
    FunctionItem(
        "Add model directory (one per kind of molecule in box)",
        DLFFLUXCondensedMenuFunctions.add_model_directory_path,
    ),
    FunctionItem(
        "Clear the selected model directories",
        DLFFLUXCondensedMenuFunctions.clear_model_directory_paths,
    ),
    SubmenuItem(
        "Change DL_POLY parameters",
        dl_poly_parameters_menu,
        dl_fflux_condensed_menu,
    ),
    FunctionItem(
        "Select number of cores",
        DLFFLUXCondensedMenuFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Select DL_FFLUX executable path (optional override)",
        DLFFLUXCondensedMenuFunctions.select_executable_path,
    ),
    FunctionItem(
        "Show simulation box composition",
        DLFFLUXCondensedMenuFunctions.show_composition,
    ),
    FunctionItem(
        "Set up and submit DL_FFLUX job to compute",
        DLFFLUXCondensedMenuFunctions.submit_dl_fflux_to_compute,
    ),
]

add_items_to_menu(dl_fflux_condensed_menu, dl_fflux_condensed_menu_items)
