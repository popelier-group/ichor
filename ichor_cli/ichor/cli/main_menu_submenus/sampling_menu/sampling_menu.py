from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.sampling_menu.sampling_submenus import (
    submit_diversity_menu,
    SUBMIT_DIVERSITY_MENU_DESCRIPTION,
    update_trajectory_information,
)
from ichor.cli.main_menu_submenus.sampling_menu.sampling_submenus.diversity_submenu import (  # noqa: E501
    job_memory_gb,
    rmsd_matrix_memory_gb,
    submit_diversity_menu_options,
    total_memory_gb,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import print_summary_and_pause
from ichor.cli.useful_functions.user_input import user_input_path


SAMPLING_MENU_DESCRIPTION = MenuDescription(
    "Sampling Menu",
    subtitle="Use this menu to perform diversity sampling on a trajectory.\n",
)


@dataclass
class SamplingMenuOptions(MenuOptions):
    selected_trajectory_path: Path = (
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
    )

    def check_selected_trajectory_path(self) -> Union[str, None]:
        """Checks whether the given Trajectory exists or if it is a file."""
        traj_path = Path(self.selected_trajectory_path)
        if not traj_path.exists():
            return f"Current trajectory path: {traj_path} does not exist."
        elif not traj_path.is_file():
            return f"Current trajectory path: {traj_path} is not a file."
        elif not traj_path.suffix == ".xyz":
            return f"Current trajectory path: {traj_path} might not be a trajectory."

    selected_xyz_path: Path = ichor.cli.global_menu_variables.SELECTED_XYZ_PATH

    def check_selected_xyz_path(self) -> Union[str, None]:
        """Checks whether the given opt xyz path exists or if it is a file."""

        xyz_path = Path(self.selected_xyz_path)
        if not xyz_path.exists():
            return f"Current opt path: {xyz_path} does not exist."
        elif not xyz_path.is_file():
            return f"Current opt path: {xyz_path} is not a file."
        elif not xyz_path.suffix == ".xyz":
            return f"Current opt path: {xyz_path} might not be a .xyz file."


# initialize dataclass for storing information for menu
sampling_menu_options = SamplingMenuOptions()


# class with static methods for each menu item that calls a function.
class SamplingFunctions:
    """Functions that run when menu items are selected"""

    @staticmethod
    def select_trajectory():
        """function that asks user to update trajectory path.

        The geometries in the trajectory are counted (without reading them all in), as
        both how large a sample can be taken from it and how large a chunk the diversity
        sampler can hold in memory depend on how long it is."""
        traj_path = user_input_path("Enter Trajectory Path: ")
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH = Path(
            traj_path
        ).absolute()
        sampling_menu_options.selected_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
        )

        ngeometries = update_trajectory_information(
            ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
        )
        # a file which could not be counted is caught by the check functions, which say
        # so in the menu prologue, so there is nothing worth reporting for it here
        if not ngeometries:
            return

        chunk_size = submit_diversity_menu_options.selected_chunk_size
        ncores = submit_diversity_menu_options.selected_number_of_cores
        print_summary_and_pause(
            "TRAJECTORY SELECTED",
            {
                "Trajectory": ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH,
                "Geometries": f"{ngeometries:,}",
                "Chunk size": f"{chunk_size:,} geometries per chunk",
                "RMSD matrix": f"about {rmsd_matrix_memory_gb(ngeometries):,.1f} GB",
                "Estimated memory": (
                    f"about {total_memory_gb(chunk_size, ngeometries):,.1f} GB in "
                    f"total, of the {job_memory_gb(ncores):,.0f} GB a {ncores} core "
                    f"job is given"
                ),
            },
            [
                "The diversity sampler works out the RMSD of every geometry against "
                "every other one and keeps the whole matrix in memory, so what it needs "
                "grows with the square of the length of the trajectory. That is the "
                "RMSD matrix above, and it is there whatever the chunk size is.",
                "The chunk size has been derived from this trajectory and the memory "
                "the job asks for, so that the two together fit; it can be changed (or "
                "pinned) in the diversity sampling menu. If the trajectory is too long "
                "to fit at all, the menu says so: it then has to be thinned (e.g. every "
                "nth step of it) or given a job with more cores, as the memory comes "
                "with the cores.",
            ],
        )

    @staticmethod
    def select_xyz():
        """Asks user to update the .xyz file and then updates the MolecularDynamicsMenuOptions instance."""
        xyz_path = user_input_path("Enter Optimised Geometry Path: ")
        ichor.cli.global_menu_variables.SELECTED_XYZ_PATH = Path(xyz_path).absolute()
        sampling_menu_options.selected_xyz_path = (
            ichor.cli.global_menu_variables.SELECTED_XYZ_PATH
        )


# initialize menu
sampling_menu = ConsoleMenu(
    this_menu_options=sampling_menu_options,
    title=SAMPLING_MENU_DESCRIPTION.title,
    subtitle=SAMPLING_MENU_DESCRIPTION.subtitle,
    prologue_text=SAMPLING_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SAMPLING_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SAMPLING_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
sampling_menu_items = [
    FunctionItem("Select path of trajectory", SamplingFunctions.select_trajectory),
    FunctionItem(
        "Select xyz file containing a single optimised geometry",
        SamplingFunctions.select_xyz,
    ),
    SubmenuItem(
        SUBMIT_DIVERSITY_MENU_DESCRIPTION.title,
        submit_diversity_menu,
        sampling_menu,
    ),
]

add_items_to_menu(sampling_menu, sampling_menu_items)
