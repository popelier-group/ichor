"""The diversity sampling menu, which picks a spread-out subset of a trajectory to send
on to the (expensive) Gaussian and AIMAll calculations.

The setting which most often goes wrong here is the chunk size, as too large a chunk gets
the job killed for running out of memory and too small a chunk makes it crawl. It is
therefore derived from the length of the trajectory and the memory a core gets on the
machine (see :func:`suggest_chunk_size`) rather than being left at a fixed default.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List, Union

import ichor.cli.global_menu_variables
import ichor.hpc.global_variables
from consolemenu.items import FunctionItem, SubmenuItem
from ichor.cli.console_menu import add_items_to_menu, ConsoleMenu
from ichor.cli.menu_description import MenuDescription
from ichor.cli.menu_options import MenuOptions
from ichor.cli.useful_functions import (
    bool_to_str,
    print_summary_and_pause,
    user_input_bool,
    user_input_free_flow,
    user_input_int,
)
from ichor.core.files import count_geometries_in_xyz
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.main.polus import submit_polus, write_diversity_sampling

SUBMIT_DIVERSITY_MENU_DESCRIPTION = MenuDescription(
    "Submit Diversity Sampling Menu",
    subtitle="Use this menu to perform diversity sampling on a trajectory.\n",
)

DIVERSITY_PARAMETERS_MENU_DESCRIPTION = MenuDescription(
    "Diversity Sampling Parameters Menu",
    subtitle="Change how the sampler treats the geometries and what it writes out.",
)

SUBMIT_DIVERSITY_MENU_DEFAULTS = {
    "default_ncores": 4,
    "default_heavy_atoms_only": False,
    "default_sample_sizes": [1000],
    "default_chunk_size": 500,
    # whether the geometries are rotated onto the seed geometry before being compared
    "default_rotate_trajectory": True,
    # the rotation method the sampler uses (a polus setting, e.g. KU)
    "default_rotation_method": "KU",
    # whether the sampler stops once the sample stops getting more diverse
    "default_auto_stop": False,
    # whether the features of chemically equivalent atoms are averaged over
    "default_group_average": False,
    # whether FEREBUS training set inputs are written out alongside the sample
    "default_write_ferebus_inputs": False,
}

# the weights vector telling the sampler which atoms count towards the distance between
# two geometries. HL1:0 leaves the hydrogens out of it, HL1:1 keeps them in.
HEAVY_ATOMS_ONLY_WEIGHTS_VECTOR = "HL1:0"
ALL_ATOMS_WEIGHTS_VECTOR = "HL1:1"

# a distance is held as a float64
BYTES_PER_DISTANCE = 8
# the fraction of a core's memory the distance block of one chunk is allowed to take,
# which leaves room for the features, the trajectory itself and the interpreter
CHUNK_MEMORY_FRACTION = 0.5
# a chunk smaller than this spends more time on the per-chunk overhead than on the
# distances it is there to compute, so suggestions are not rounded below it (a trajectory
# long enough that even this does not fit in memory is given whatever does)
MINIMUM_SUGGESTED_CHUNK_SIZE = 50
# suggested chunk sizes are rounded down to a multiple of this, as a tidy number is
# easier to recognise as a suggestion (and the estimate is not precise enough to warrant
# suggesting e.g. 537 geometries)
CHUNK_SIZE_ROUNDING = 50
# used when the machine is not in the config (e.g. running the menu on a laptop), where
# a small budget is the safe way to be wrong
FALLBACK_MEMORY_PER_CORE_GB = 4


def memory_per_core_gb() -> float:
    """Returns the memory (in GB) that one core is given on this machine, which is what
    the memory a diversity sampling job can use is set by: the batch system hands out
    memory per core, and the sampler works on one chunk per core."""

    return get_param_from_config(
        ichor.hpc.global_variables.ICHOR_CONFIG,
        ichor.hpc.global_variables.MACHINE,
        "hpc",
        "memory_per_core_gb",
        default=FALLBACK_MEMORY_PER_CORE_GB,
    )


def chunk_memory_gb(chunk_size: int, ngeometries: int) -> float:
    """Returns the memory (in GB) one worker of the sampler needs for a chunk of the
    given size.

    Comparing a chunk against the trajectory needs a distance for every pair of a
    geometry in the chunk and a geometry in the trajectory, and that block of distances
    is far and away the largest thing the sampler holds, so it is what the estimate is
    made of.

    :param chunk_size: The number of geometries compared at a time.
    :param ngeometries: The number of geometries in the trajectory.
    """

    return chunk_size * ngeometries * BYTES_PER_DISTANCE / 1024**3


def suggest_chunk_size(ngeometries: int) -> int:
    """Returns a chunk size whose distance block (see :func:`chunk_memory_gb`) fits in
    the memory one core is given on this machine.

    Every worker of the sampler holds a block of its own, and the batch system gives out
    memory per core, so the budget to fit in is the memory of a single core no matter how
    many cores the job asks for. Asking for more cores therefore makes the job faster but
    does not allow a larger chunk.

    :param ngeometries: The number of geometries in the trajectory. If this is not known
        (0), the menu default is returned instead.
    """

    if ngeometries <= 0:
        return SUBMIT_DIVERSITY_MENU_DEFAULTS["default_chunk_size"]

    budget_bytes = CHUNK_MEMORY_FRACTION * memory_per_core_gb() * 1024**3
    chunk_size = int(budget_bytes // (ngeometries * BYTES_PER_DISTANCE))

    # a trajectory long enough that not even the smallest worthwhile chunk fits is
    # suggested the largest chunk that does, as a slow job is still better than one which
    # is killed for running out of memory
    if chunk_size < MINIMUM_SUGGESTED_CHUNK_SIZE:
        return max(1, chunk_size)

    # round down to a tidy number, as the estimate is not precise enough to warrant
    # suggesting an exact one, and never chunk past the end of the trajectory
    chunk_size -= chunk_size % CHUNK_SIZE_ROUNDING

    return min(ngeometries, chunk_size)


def parse_sample_sizes(text: str) -> List[int]:
    """Parses the sample sizes the user typed in, which are one or more positive whole
    numbers separated by commas (or spaces).

    :param text: What the user typed, e.g. ``500, 1000, 2000``.
    :raises ValueError: If nothing, or something which is not a positive whole number,
        was given.
    :return: The sizes, in order and without duplicates.
    """

    sizes = [int(part) for part in text.replace(",", " ").split()]

    if not sizes:
        raise ValueError("no sample sizes were given")
    if any(size < 1 for size in sizes):
        raise ValueError("a sample size must be 1 or greater")

    return sorted(set(sizes))


# dataclass used to store values for SubmitDiversityMenu
@dataclass
class SubmitDiversityMenuOptions(MenuOptions):
    selected_number_of_cores: int
    # whether the hydrogens are left out of the distance between two geometries
    selected_heavy_atoms_only: bool
    # one or more sample sizes, all written out in the one pass over the trajectory
    selected_sample_sizes: List[int]
    # the number of geometries compared at a time, which is what the memory the job needs
    # is set by
    selected_chunk_size: int
    # how the geometries are treated and what is written out
    selected_rotate_trajectory: bool
    selected_rotation_method: str
    selected_auto_stop: bool
    selected_group_average: bool
    selected_write_ferebus_inputs: bool
    # the geometries in the selected trajectory, counted when it is selected so that the
    # sample and chunk sizes can be checked (and suggested) against it. 0 = not known
    number_of_geometries_in_file: int

    def check_selected_number_of_cores(self) -> Union[str, None]:
        """Checks that the job asks for at least one core."""
        if self.selected_number_of_cores < 1:
            return (
                f"Current number of cores: {self.selected_number_of_cores} "
                "must be 1 or greater."
            )

    def check_selected_sample_sizes(self) -> Union[str, None]:
        """Checks the sample sizes are positive and that there are enough geometries in
        the trajectory to take the largest of them from."""
        if not self.selected_sample_sizes:
            return "No sample sizes are selected."
        if any(size < 1 for size in self.selected_sample_sizes):
            return f"Current sample sizes: {self.selected_sample_sizes} must be 1 or greater."  # noqa: E501

        largest_sample = max(self.selected_sample_sizes)
        if (
            self.number_of_geometries_in_file
            and largest_sample > self.number_of_geometries_in_file
        ):
            return (
                f"Current sample size: {largest_sample:,} is larger than the "
                f"{self.number_of_geometries_in_file:,} geometries in the trajectory."
            )

    def check_selected_chunk_size(self) -> Union[str, None]:
        """Checks the chunk size is positive, is not larger than the trajectory, and
        that the distance block it leads to fits in the memory of a core."""
        if self.selected_chunk_size < 1:
            return (
                f"Current chunk size: {self.selected_chunk_size} must be 1 or greater."
            )

        if not self.number_of_geometries_in_file:
            return None

        if self.selected_chunk_size > self.number_of_geometries_in_file:
            return (
                f"Current chunk size: {self.selected_chunk_size:,} is larger than the "
                f"{self.number_of_geometries_in_file:,} geometries in the trajectory."
            )

        needed_gb = chunk_memory_gb(
            self.selected_chunk_size, self.number_of_geometries_in_file
        )
        available_gb = memory_per_core_gb()
        if needed_gb > CHUNK_MEMORY_FRACTION * available_gb:
            return (
                f"Current chunk size: {self.selected_chunk_size:,} needs about "
                f"{needed_gb:.1f} GB per core of the {available_gb} GB a core gets, so "
                f"the job may be killed for running out of memory. "
                f"{suggest_chunk_size(self.number_of_geometries_in_file):,} would fit."
            )

    def check_selected_rotation_method(self) -> Union[str, None]:
        """Checks that a rotation method is given when the trajectory is rotated."""
        if self.selected_rotate_trajectory and not self.selected_rotation_method:
            return "No rotation method is selected, but the trajectory is rotated."


# initialize dataclass for storing information for menu
submit_diversity_menu_options = SubmitDiversityMenuOptions(
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_ncores"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_heavy_atoms_only"],
    list(SUBMIT_DIVERSITY_MENU_DEFAULTS["default_sample_sizes"]),
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_chunk_size"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_rotate_trajectory"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_rotation_method"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_auto_stop"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_group_average"],
    SUBMIT_DIVERSITY_MENU_DEFAULTS["default_write_ferebus_inputs"],
    0,
)

# the chunk size follows the length of the trajectory unless the user picks one by hand,
# in which case their choice is kept even when a different trajectory is selected
chunk_size_overridden = False


def update_trajectory_information(trajectory_path: Union[Path, str]) -> int:
    """Counts the geometries in the newly selected trajectory (without reading them all
    in) and, unless the chunk size was picked by hand, derives the chunk size from it.

    This is called by the parent sampling menu, as the trajectory is selected there but
    it is this menu whose settings depend on how long it is.

    :param trajectory_path: The trajectory that was selected.
    :return: The number of geometries counted (0 if the file could not be read, e.g. it
        does not exist yet or is not a .xyz file, which the menu checks warn about).
    """

    try:
        ngeometries = count_geometries_in_xyz(trajectory_path)
    except (OSError, ValueError):
        # an unreadable file (or one which is not an xyz) is caught by the check
        # functions, which say so in the menu prologue
        ngeometries = 0

    submit_diversity_menu_options.number_of_geometries_in_file = ngeometries

    if not chunk_size_overridden:
        submit_diversity_menu_options.selected_chunk_size = suggest_chunk_size(
            ngeometries
        )

    return ngeometries


def weights_vector() -> str:
    """Returns the weights vector for the atoms the sample is made diverse over."""

    if submit_diversity_menu_options.selected_heavy_atoms_only:
        return HEAVY_ATOMS_ONLY_WEIGHTS_VECTOR

    return ALL_ATOMS_WEIGHTS_VECTOR


# class with static methods for each menu item that calls a function.
class SubmitDiversityFunctions:
    @staticmethod
    def select_number_of_cores():
        """Asks user to select the number of cores. The sampler works on one chunk per
        core, so more cores make the job faster; they do not allow a larger chunk, as the
        memory each core gets is fixed."""
        submit_diversity_menu_options.selected_number_of_cores = user_input_int(
            "Enter number of cores: ",
            submit_diversity_menu_options.selected_number_of_cores,
            minimum=1,
        )

    @staticmethod
    def select_heavy_atoms_only():
        """Asks whether the geometries are compared over the heavy atoms only, i.e.
        whether the hydrogens are left out of the weights vector."""
        submit_diversity_menu_options.selected_heavy_atoms_only = user_input_bool(
            "Restrict to heavy atoms (yes/no): ",
            submit_diversity_menu_options.selected_heavy_atoms_only,
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity sampling restricted to heavy atoms"
            f" {submit_diversity_menu_options.selected_heavy_atoms_only}"
            f" (weights vector {weights_vector()})"
        )

    @staticmethod
    def select_sample_sizes():
        """Asks user for the size of the sampled pool. Several sizes can be given at once
        (separated by commas), which writes out a sample of each size in the one pass
        over the trajectory rather than having to sample it again per size."""
        while True:
            answer = user_input_free_flow(
                "Sample pool size(s), comma separated (e.g. 500,1000,2000): ",
                None,
            )
            # nothing typed keeps the sizes that are already selected
            if answer is None:
                return
            try:
                sizes = parse_sample_sizes(answer)
            except ValueError:
                print("Enter one or more whole numbers of 1 or greater, e.g. 500,1000")
                continue
            submit_diversity_menu_options.selected_sample_sizes = sizes
            break

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            "Diversity sample pool sizes "
            f"{submit_diversity_menu_options.selected_sample_sizes}"
        )

    @staticmethod
    def select_chunk_size():
        """Asks user to select the chunk size, i.e. how many geometries are compared
        against the trajectory at a time. This is what sets how much memory the job needs
        (see :func:`chunk_memory_gb`), so too large a chunk gets the job killed and too
        small a chunk makes it slow.

        The chunk size is derived from the length of the trajectory and the memory a core
        gets (see :func:`suggest_chunk_size`) unless it is given here, in which case the
        given value is kept even when a different trajectory is selected. Entering 0 goes
        back to deriving it."""
        global chunk_size_overridden

        ngeometries = submit_diversity_menu_options.number_of_geometries_in_file
        suggested = suggest_chunk_size(ngeometries)

        if ngeometries:
            print(
                f"Suggested chunk size for the {ngeometries:,} geometries in the "
                f"trajectory: {suggested:,} "
                f"(about {chunk_memory_gb(suggested, ngeometries):.1f} GB per core of "
                f"the {memory_per_core_gb()} GB a core gets)"
            )

        chunk_size = user_input_int(
            "Enter chunk size (0 = derive from the trajectory and memory): ",
            submit_diversity_menu_options.selected_chunk_size,
            minimum=0,
        )
        # a chunk size which is (or is asked to be) the derived one is not an override, so
        # selecting a different trajectory later is still free to update it
        chunk_size_overridden = bool(chunk_size) and chunk_size != suggested
        submit_diversity_menu_options.selected_chunk_size = chunk_size or suggested

        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity chunk size {submit_diversity_menu_options.selected_chunk_size}"
        )

    @staticmethod
    def select_rotate_trajectory():
        """Asks whether the geometries are rotated onto the seed geometry before they are
        compared, so that two geometries of the same shape in different orientations do
        not count as being different from one another."""
        submit_diversity_menu_options.selected_rotate_trajectory = user_input_bool(
            "Rotate trajectory onto the seed geometry (yes/no): ",
            submit_diversity_menu_options.selected_rotate_trajectory,
        )

    @staticmethod
    def select_rotation_method():
        """Asks for the method used to rotate the geometries onto the seed geometry.
        This is passed straight to the sampler (``rotMethod``), so it has to be one of the
        methods polus knows about; the default is KU."""
        submit_diversity_menu_options.selected_rotation_method = user_input_free_flow(
            "Enter rotation method (e.g. KU): ",
            submit_diversity_menu_options.selected_rotation_method,
        )

    @staticmethod
    def select_auto_stop():
        """Asks whether the sampler stops on its own once the sample has stopped getting
        more diverse, rather than always taking the full sample size."""
        submit_diversity_menu_options.selected_auto_stop = user_input_bool(
            "Stop early once the sample stops getting more diverse (yes/no): ",
            submit_diversity_menu_options.selected_auto_stop,
        )

    @staticmethod
    def select_group_average():
        """Asks whether the features of chemically equivalent atoms are averaged over,
        which stops a sample being made diverse over differences that are only a
        relabelling of equivalent atoms (e.g. the hydrogens of a methyl group)."""
        submit_diversity_menu_options.selected_group_average = user_input_bool(
            "Average over chemically equivalent atoms (yes/no): ",
            submit_diversity_menu_options.selected_group_average,
        )

    @staticmethod
    def select_write_ferebus_inputs():
        """Asks whether FEREBUS training set inputs are written out alongside the sampled
        trajectory."""
        submit_diversity_menu_options.selected_write_ferebus_inputs = user_input_bool(
            "Write FEREBUS inputs as well (yes/no): ",
            submit_diversity_menu_options.selected_write_ferebus_inputs,
        )

    @staticmethod
    def submit_diversity_on_compute():
        """Writes the diversity sampling script and submits it to a compute node."""

        ncores = submit_diversity_menu_options.selected_number_of_cores
        sample_sizes = submit_diversity_menu_options.selected_sample_sizes
        chunk_size = submit_diversity_menu_options.selected_chunk_size
        ngeometries = submit_diversity_menu_options.number_of_geometries_in_file

        xyz_path = Path(ichor.cli.global_menu_variables.SELECTED_XYZ_PATH)
        trajectory_path = Path(ichor.cli.global_menu_variables.SELECTED_TRAJECTORY_PATH)

        # the paths are selected in the parent menu, so they can still be unset (or wrong)
        # by the time the job is submitted from here
        problem = None
        if not trajectory_path.is_file():
            problem = f"The trajectory {trajectory_path} is not a file."
        elif not xyz_path.is_file():
            problem = f"The seed geometry {xyz_path} is not a file."
        elif sample_sizes and ngeometries and max(sample_sizes) > ngeometries:
            problem = (
                f"The largest sample size ({max(sample_sizes):,}) is larger than the "
                f"{ngeometries:,} geometries in the trajectory."
            )

        if problem:
            ichor.hpc.global_variables.LOGGER.error(
                f"Diversity sampling not submitted: {problem}"
            )
            print_summary_and_pause(
                "DIVERSITY SAMPLING NOT SUBMITTED",
                {
                    "Trajectory": trajectory_path,
                    "Seed geometry": xyz_path,
                    "Reason": problem,
                },
                [
                    "The trajectory to sample and the seed geometry to start from are "
                    "both selected in the sampling menu above this one, so go back and "
                    "select them before submitting.",
                ],
            )
            return

        # the sampler works on one chunk per core, so it is only worth running in
        # parallel when the job has more than the one core to run them on
        parallel = ncores > 1

        div_script = write_diversity_sampling(
            filename=trajectory_path,
            seed_geom=xyz_path,
            weights_vector=weights_vector(),
            sample_size=sample_sizes,
            chunk_size=chunk_size,
            rotate_traj=submit_diversity_menu_options.selected_rotate_trajectory,
            rot_method=submit_diversity_menu_options.selected_rotation_method,
            auto_stop=submit_diversity_menu_options.selected_auto_stop,
            group_average=submit_diversity_menu_options.selected_group_average,
            write_ferebus_inputs=(
                submit_diversity_menu_options.selected_write_ferebus_inputs
            ),
            parallel=parallel,
        )

        job_id = submit_polus(
            input_script=div_script,
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES["diversity_sampling"],
            ncores=ncores,
        )

        print_summary_and_pause(
            "DIVERSITY SAMPLING JOB SUBMITTED",
            {
                "Trajectory": trajectory_path,
                "Geometries in trajectory": (
                    f"{ngeometries:,}" if ngeometries else "not known"
                ),
                "Seed geometry": xyz_path,
                # the input script sits in the folder the sampling writes its output to
                "Run directory": Path(div_script).parent,
                "Job ID": job_id.id if job_id else "not available",
                "Sample sizes": (
                    ", ".join(f"{size:,}" for size in sample_sizes) + " geometries"
                ),
                "Chunk size": f"{chunk_size:,} geometries per chunk",
                "Estimated memory": (
                    f"about {chunk_memory_gb(chunk_size, ngeometries):.1f} GB per core "
                    f"of the {memory_per_core_gb()} GB a core gets"
                    if ngeometries
                    else "not known (the trajectory could not be counted)"
                ),
                "Weights vector": f"{weights_vector()} "
                f"({'heavy atoms only' if submit_diversity_menu_options.selected_heavy_atoms_only else 'all atoms, hydrogens included'})",  # noqa: E501
                "Rotation": (
                    f"onto the seed geometry "
                    f"({submit_diversity_menu_options.selected_rotation_method})"
                    if submit_diversity_menu_options.selected_rotate_trajectory
                    else "none (geometries compared as they are)"
                ),
                "Stop early": (
                    "yes, once the sample stops getting more diverse"
                    if submit_diversity_menu_options.selected_auto_stop
                    else "no, the full sample is taken"
                ),
                "Group average": bool_to_str(
                    submit_diversity_menu_options.selected_group_average
                ),
                "FEREBUS inputs": bool_to_str(
                    submit_diversity_menu_options.selected_write_ferebus_inputs
                ),
                "CPU cores": f"{ncores} ({'parallel' if parallel else 'serial'})",
            },
            [
                "Diversity sampling picks a spread-out subset of the trajectory, so "
                "that the geometries which go on to expensive Gaussian and AIMAll "
                "calculations cover the configuration space rather than repeating "
                "similar structures.",
                "The trajectory is compared in chunks to keep the distance matrix in "
                "memory, so a smaller chunk size uses less memory but takes longer. "
                "Each core works on a chunk of its own and the batch system gives out "
                "memory per core, so asking for more cores makes the job faster but "
                "does not let it hold a larger chunk.",
                "The job is now queued on a compute node, so it will not start "
                "immediately and this menu does not wait for it. Check on it with your "
                "batch system's queue command (e.g. qstat / squeue); the sampled "
                "trajectory is written into the run directory above.",
            ],
        )
        # update logger
        ichor.hpc.global_variables.LOGGER.info(
            f"Diversity sampling job submitted for {xyz_path}"
        )


# initialize menus
submit_diversity_menu = ConsoleMenu(
    this_menu_options=submit_diversity_menu_options,
    title=SUBMIT_DIVERSITY_MENU_DESCRIPTION.title,
    subtitle=SUBMIT_DIVERSITY_MENU_DESCRIPTION.subtitle,
    prologue_text=SUBMIT_DIVERSITY_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=SUBMIT_DIVERSITY_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=SUBMIT_DIVERSITY_MENU_DESCRIPTION.show_exit_option,
)

# submenu grouping the settings which are usually left alone, to keep the main menu
# short. It has no options dataclass of its own (its functions edit the main menu's
# options, which are displayed via the parent menu's prologue).
diversity_parameters_menu = ConsoleMenu(
    title=DIVERSITY_PARAMETERS_MENU_DESCRIPTION.title,
    subtitle=DIVERSITY_PARAMETERS_MENU_DESCRIPTION.subtitle,
    prologue_text=DIVERSITY_PARAMETERS_MENU_DESCRIPTION.prologue_description_text,
    epilogue_text=DIVERSITY_PARAMETERS_MENU_DESCRIPTION.epilogue_description_text,
    show_exit_option=DIVERSITY_PARAMETERS_MENU_DESCRIPTION.show_exit_option,
)

# make menu items
# can use lambda functions to change text of options as well :)
diversity_parameters_menu_items = [
    FunctionItem(
        "Rotate trajectory onto the seed geometry",
        SubmitDiversityFunctions.select_rotate_trajectory,
    ),
    FunctionItem(
        "Change rotation method",
        SubmitDiversityFunctions.select_rotation_method,
    ),
    FunctionItem(
        "Stop early once the sample stops getting more diverse",
        SubmitDiversityFunctions.select_auto_stop,
    ),
    FunctionItem(
        "Average over chemically equivalent atoms",
        SubmitDiversityFunctions.select_group_average,
    ),
    FunctionItem(
        "Write FEREBUS inputs as well",
        SubmitDiversityFunctions.select_write_ferebus_inputs,
    ),
]
add_items_to_menu(diversity_parameters_menu, diversity_parameters_menu_items)

submit_diversity_menu_items = [
    FunctionItem(
        "Change cores",
        SubmitDiversityFunctions.select_number_of_cores,
    ),
    FunctionItem(
        "Change atoms compared (all atoms / heavy atoms only)",
        SubmitDiversityFunctions.select_heavy_atoms_only,
    ),
    FunctionItem(
        "Change sample size(s)",
        SubmitDiversityFunctions.select_sample_sizes,
    ),
    FunctionItem(
        "Change chunk size (0 = derive from the trajectory and memory)",
        SubmitDiversityFunctions.select_chunk_size,
    ),
    SubmenuItem(
        DIVERSITY_PARAMETERS_MENU_DESCRIPTION.title,
        diversity_parameters_menu,
        submit_diversity_menu,
    ),
    FunctionItem(
        "Submit diversity sampler",
        SubmitDiversityFunctions.submit_diversity_on_compute,
    ),
]

add_items_to_menu(submit_diversity_menu, submit_diversity_menu_items)
