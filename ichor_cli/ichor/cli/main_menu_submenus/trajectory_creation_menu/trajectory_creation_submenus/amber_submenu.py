from dataclasses import dataclass
from pathlib import Path

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_float,
    user_input_free_flow,
    user_input_int,
    user_input_path,
)
from ichor.core.molecular_dynamics.amber import mdcrd_to_xyz
from ichor.hpc.molecular_dynamics import submit_amber

# TODO: possibly make this be read from a file
AMBER_MENU_DEFAULTS = {
    "default_temperature": 1000,
    "default_number_of_timesteps": 1_000_000,
    "default_write_coord_every": 10,
    "default_dt": 0.001,
    "default_ln_gamma": 0.7,
}

AMBER_MENU_DESCRIPTION = MenuDescription(
    "AMBER Menu", subtitle="Use this to submit AMBER simulations."
)


def ask_user_for_mdcrd_paths():

    default_every = 1

    amber_directory_path = user_input_path("Give path to AMBER directory: ")
    system_name = user_input_free_flow("Give name of system: ")
    system_name = system_name.upper()
    every = user_input_int(
        f"Write out every nth timestep (give n), default {default_every}: "
    )
    if every is None:
        every = default_every

    return Path(amber_directory_path), system_name, every


@dataclass
class AmberMenuOptions(MenuOptions):
    selected_temperature: int
    selected_number_of_timesteps: int
    selected_write_coordinates_every_nth_timestep: int
    selected_dt: float
    selected_ln_gamma: float


amber_menu_options = AmberMenuOptions(*AMBER_MENU_DEFAULTS.values())


# class with static methods for each menu item that calls a function.
class AmberMenuFunctions:
    @staticmethod
    def select_temperature():
        """
        Select temperature of AMBER simulation.
        """
        amber_menu_options.selected_temperature = user_input_int(
            "Select temperature: ", amber_menu_options.selected_temperature
        )

    @staticmethod
    def select_number_of_timesteps():
        """
        Selects the number of timesteps in AMBER simulation.
        """
        amber_menu_options.selected_number_of_timesteps = user_input_int(
            "Select number of timesteps:",
            amber_menu_options.selected_number_of_timesteps,
        )

    @staticmethod
    def select_write_every_nth_timestep():
        """
        Select how often to write xyz coordinates from AMBER simulation.
        """
        amber_menu_options.selected_write_coordinates_every_nth_timestep = (
            user_input_int(
                "Select write coordinates every nth step:",
                amber_menu_options.selected_write_coordinates_every_nth_timestep,
            )
        )

    @staticmethod
    def select_dt():
        """
        Select the delta t for the timestep of AMBER.
        """
        amber_menu_options.selected_dt = user_input_float(
            "Selected dt: ", amber_menu_options.selected_dt
        )

    @staticmethod
    def select_ln_gamma():
        """
        Select the ln_gamma of AMBER. Check the manual for description.
        """
        amber_menu_options.selected_ln_gamma = user_input_float(
            "Select ln gamma: ", amber_menu_options.selected_ln_gamma
        )

    @staticmethod
    def submit_amber_to_compute():
        """Asks for user input and submits AMBER job to compute node."""

        temperature = amber_menu_options.selected_temperature
        nsteps = amber_menu_options.selected_number_of_timesteps
        write_coord_every = (
            amber_menu_options.selected_write_coordinates_every_nth_timestep
        )
        dt = amber_menu_options.selected_dt
        ln_gamma = amber_menu_options.selected_ln_gamma

        xyz_path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH

        job_id = submit_amber(
            input_file_path=xyz_path,
            temperature=temperature,
            nsteps=nsteps,
            write_coord_every=write_coord_every,
            system_name=xyz_path.stem,
            dt=dt,
            ln_gamma=ln_gamma,
        )

        amber_directory = Path(ichor.hpc.global_variables.FILE_STRUCTURE["amber"])

        print_summary_and_pause(
            "AMBER JOB SUBMITTED",
            {
                "Starting geometry": xyz_path,
                "System name": xyz_path.stem,
                "AMBER directory": amber_directory,
                "Job ID": job_id.id if job_id else "not available",
                "Temperature": f"{temperature} K",
                "Timesteps": f"{nsteps:,}",
                "Timestep length": f"{dt} ps",
                "Simulated time": f"{nsteps * dt:,.1f} ps",
                "Write coordinates": f"every {write_coord_every} timestep(s), "
                f"~{nsteps // write_coord_every:,} geometries",
                "Collision frequency": f"{ln_gamma} ps",
            },
            [
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue).",
                "The mol2 and md.in input files are in the AMBER directory above, and "
                "the trajectory is written there as an mdcrd file. Use 'Convert mdcrd "
                "to xyz' once the job has finished to turn it into a trajectory ichor "
                "can split into a PointsDirectory.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            "AMBER trajectory generation job submitted"
        )

    @staticmethod
    def xyz_from_mdcrd():
        amber_path, system_name, every = ask_user_for_mdcrd_paths()

        mdcrd_file = prmtop_file = mdin_file = None
        for f in amber_path.iterdir():
            if f.stem == "mdcrd":
                mdcrd_file = f
            elif f.suffix == ".prmtop":
                prmtop_file = f
            elif f.name == "md.in":
                mdin_file = f

        # all three are needed: the coordinates, the atom names, and the temperature
        # that the output file is named after
        missing = [
            name
            for name, found in (
                ("mdcrd", mdcrd_file),
                (".prmtop", prmtop_file),
                ("md.in", mdin_file),
            )
            if found is None
        ]
        if missing:
            print_summary_and_pause(
                "TRAJECTORY NOT CONVERTED",
                {
                    "AMBER directory": amber_path,
                    "Missing files": ", ".join(missing),
                },
                [
                    "The conversion needs the mdcrd (coordinates), the .prmtop (atom "
                    "names) and the md.in (temperature) files of a finished AMBER run, "
                    "and the files above were not found in the directory given.",
                    "Check that the AMBER job has finished and that the directory "
                    "given is the one it ran in.",
                ],
            )
            return

        mdcrd_to_xyz(mdcrd_file, prmtop_file, mdin_file, system_name, every)

        print_summary_and_pause(
            "TRAJECTORY CONVERTED TO XYZ",
            {
                "AMBER directory": amber_path,
                "System name": system_name,
                "Written every": f"{every} timestep(s)",
                "Output file": f"{system_name}-amber<temperature>K.xyz in "
                f"{Path.cwd()}",
            },
            [
                "The mdcrd trajectory has been written out as an xyz trajectory, named "
                "after the system and the temperature read from md.in.",
                "This xyz file is what the points directory menu splits into a "
                "PointsDirectory for Gaussian and AIMAll calculations.",
            ],
        )


# initialize menu
amber_menu = ConsoleMenu(
    this_menu_options=amber_menu_options,
    title=AMBER_MENU_DESCRIPTION.title,
    subtitle=AMBER_MENU_DESCRIPTION.subtitle,
    prologue_text=AMBER_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=AMBER_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=AMBER_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
amber_menu_items = [
    FunctionItem(
        "Select simulation temperature",
        AmberMenuFunctions.select_temperature,
    ),
    FunctionItem(
        "Select number of timesteps",
        AmberMenuFunctions.select_number_of_timesteps,
    ),
    FunctionItem(
        "Select write coordinates every nth timestep",
        AmberMenuFunctions.select_write_every_nth_timestep,
    ),
    FunctionItem(
        "Select dt",
        AmberMenuFunctions.select_dt,
    ),
    FunctionItem(
        "Select ln_gamma",
        AmberMenuFunctions.select_ln_gamma,
    ),
    FunctionItem(
        "Submit AMBER simulation",
        AmberMenuFunctions.submit_amber_to_compute,
    ),
    FunctionItem(
        "Convert mdcrd to xyz",
        AmberMenuFunctions.xyz_from_mdcrd,
    ),
]

add_items_to_menu(amber_menu, amber_menu_items)
