import math
from dataclasses import dataclass
from pathlib import Path
from typing import Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.main_menu_submenus.sampling_menu.sampling_submenus import (
    submit_diversity_menu,
    SUBMIT_DIVERSITY_MENU_DESCRIPTION,
    update_trajectory_information,
)
from ichor.cli.main_menu_submenus.sampling_menu.sampling_submenus.diversity_submenu import (  # noqa: E501
    format_memory_gb,
    job_memory_gb,
    largest_trajectory_for,
    peak_memory_gb,
    process_copies,
    rmsd_matrix_memory_gb,
    submit_diversity_menu_options,
)
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    print_summary_and_pause,
    user_input_free_flow,
    user_input_int,
    xyz_file_selected,
)
from ichor.cli.useful_functions.user_input import user_input_path
from ichor.core.files import thin_xyz


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
                "RMSD matrix": format_memory_gb(rmsd_matrix_memory_gb(ngeometries)),
                "Estimated memory": (
                    f"{format_memory_gb(peak_memory_gb(chunk_size, ngeometries, ncores))}"  # noqa: E501
                    f" over the {process_copies(ncores)} processes of a {ncores} core "
                    f"job, which is given {job_memory_gb(ncores):,.0f} GB"
                ),
            },
            [
                "The diversity sampler works out the RMSD of every geometry against "
                "every other one and keeps the whole matrix in memory, so what it needs "
                "grows with the square of the length of the trajectory. That is the "
                "RMSD matrix above, and it is there whatever the chunk size is.",
                "The chunk size has been derived from this trajectory and the memory "
                "the job asks for, so that the two together fit; it can be changed (or "
                "pinned) in the diversity sampling menu.",
                "The sampler forks a worker process per core once it is already holding "
                "the matrix, and what it holds is charged against the job again for "
                "every one of them, which is why the estimate above is counted over the "
                "processes. Asking for more cores therefore brings little more memory "
                "than it takes: if the trajectory is too long to fit, the menu says so "
                "and thinning it is the way out.",
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

    @staticmethod
    def thin_trajectory():
        """Writes a shorter copy of the selected trajectory and selects it in its place,
        for a trajectory which is too long for the sampler to hold the RMSD matrix of.

        There are two ways of dropping geometries, which suit different trajectories, so
        both are asked for (and can be combined):

        * keeping every nth geometry spreads what is kept over the whole trajectory,
          which is the one to use for a trajectory in which the order is time (e.g. the
          output of a metadynamics run);
        * keeping only the first n cuts the tail off, which is the one to use when the
          trajectory is already ordered by how much each geometry adds (e.g. the output
          of a previous diversity sampling, whose geometries are written in the order
          they were picked, most diverse first).

        The original trajectory is not touched, so a thinning which turns out to be too
        aggressive can be done again from it.
        """

        trajectory_path = Path(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)
        ngeometries = submit_diversity_menu_options.number_of_geometries_in_file

        if not xyz_file_selected(
            trajectory_path,
            "thin the trajectory",
            select_with="Use 'Select path of trajectory' in this menu first.",
        ):
            return

        # the trajectory is a real one, but how many geometries it holds is only counted
        # when it is selected through this menu, and the thinning is worked out from that
        if not ngeometries:
            print_summary_and_pause(
                "TRAJECTORY NOT THINNED",
                {
                    "Trajectory": trajectory_path,
                    "Reason": "No geometries could be counted in the trajectory.",
                },
                [
                    "Select the trajectory to thin in this menu first; how many "
                    "geometries it holds is counted when it is selected, which is what "
                    "the thinning is worked out from.",
                ],
            )
            return

        ncores = submit_diversity_menu_options.selected_number_of_cores
        # the longest trajectory the sampler could hold the RMSD matrix of, which is what
        # the trajectory has to come down to
        target = largest_trajectory_for(ncores)
        suggested_stride = max(1, math.ceil(ngeometries / target)) if target else 1

        print(
            f"The trajectory holds {ngeometries:,} geometries. A {ncores} core job can "
            f"sample up to about {target:,} of them, so keeping every "
            f"{suggested_stride:,} of them would bring it down to about "
            f"{math.ceil(ngeometries / suggested_stride):,}."
        )

        stride = user_input_int(
            "Keep every nth geometry (1 = keep every one): ",
            suggested_stride,
            minimum=1,
        )
        max_geometries = user_input_int(
            "Then keep at most how many of them (0 = no limit): ",
            0,
            minimum=0,
        )

        # how many geometries the answers will leave, which names the file written
        expected = math.ceil(ngeometries / stride)
        if max_geometries:
            expected = min(expected, max_geometries)

        # writing a copy of the whole trajectory under a new name helps nobody
        if expected >= ngeometries:
            print_summary_and_pause(
                "TRAJECTORY NOT THINNED",
                {
                    "Trajectory": trajectory_path,
                    "Geometries": f"{ngeometries:,}",
                    "Reason": "That would keep every geometry in the trajectory.",
                },
                [
                    "Nothing has been written, as the answers given would only copy the "
                    "trajectory. Keep every nth geometry (with n of 2 or more) or put a "
                    "limit on how many are kept to make it shorter.",
                ],
            )
            return

        default_output = (
            trajectory_path.parent / f"{trajectory_path.stem}-THINNED-{expected}.xyz"
        )
        output_path = Path(
            user_input_free_flow(
                f"Write the thinned trajectory to [{default_output.name}]: ",
                str(default_output),
            )
        )
        # a name on its own is written next to the trajectory it is made from
        if not output_path.is_absolute():
            output_path = trajectory_path.parent / output_path

        try:
            nwritten = thin_xyz(
                trajectory_path,
                output_path,
                stride=stride,
                max_geometries=max_geometries or None,
            )
        except (OSError, ValueError) as error:
            ichor.hpc.global_variables.LOGGER.error(f"Trajectory not thinned: {error}")
            print_summary_and_pause(
                "TRAJECTORY NOT THINNED",
                {
                    "Trajectory": trajectory_path,
                    "Thinned trajectory": output_path,
                    "Reason": error,
                },
                [
                    "The original trajectory has not been touched, so the thinning can "
                    "be tried again with a different file to write to.",
                ],
            )
            return

        # the thinned trajectory is the one to sample from now, so select it (which also
        # counts it and derives the chunk size from its length)
        ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH = (
            output_path.absolute()
        )
        sampling_menu_options.selected_trajectory_path = (
            ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
        )
        update_trajectory_information(
            ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH
        )

        chunk_size = submit_diversity_menu_options.selected_chunk_size
        ichor.hpc.global_variables.LOGGER.info(
            f"Thinned {trajectory_path} ({ngeometries} geometries) to {output_path} "
            f"({nwritten} geometries)"
        )
        print_summary_and_pause(
            "TRAJECTORY THINNED",
            {
                "Original trajectory": trajectory_path,
                "Thinned trajectory": output_path,
                "Geometries": f"{nwritten:,} of the original {ngeometries:,}",
                "Kept": (
                    f"every {stride:,} geometries" if stride > 1 else "every geometry"
                )
                + (f", up to the first {max_geometries:,}" if max_geometries else ""),
                "RMSD matrix": format_memory_gb(rmsd_matrix_memory_gb(nwritten)),
                "Estimated memory": (
                    f"{format_memory_gb(peak_memory_gb(chunk_size, nwritten, ncores))}"  # noqa: E501
                    f" over the {process_copies(ncores)} processes of a {ncores} core "
                    f"job, which is given {job_memory_gb(ncores):,.0f} GB"
                ),
            },
            [
                "The thinned trajectory is now the selected one, so the diversity "
                "sampling menu will sample from it. The original is untouched, so this "
                "can be done again from it if too much (or too little) came off.",
                "The chunk size has been derived again from the shorter trajectory.",
            ],
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
    FunctionItem(
        "Thin the trajectory (write a shorter .xyz and select it)",
        SamplingFunctions.thin_trajectory,
    ),
    SubmenuItem(
        SUBMIT_DIVERSITY_MENU_DESCRIPTION.title,
        submit_diversity_menu,
        sampling_menu,
    ),
]

add_items_to_menu(sampling_menu, sampling_menu_items)
