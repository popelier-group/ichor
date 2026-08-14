"""The diversity sampling menu, which picks a spread-out subset of a trajectory to send
on to the (expensive) Gaussian and AIMAll calculations.

The setting which most often goes wrong here is the chunk size, as too large a chunk gets
the job killed for running out of memory and too small a chunk makes it crawl. It is
therefore derived from the length of the trajectory and the memory a core gets on the
machine (see :func:`suggest_chunk_size`) rather than being left at a fixed default.
"""

import math
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
    user_input_restricted,
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
# two geometries. It is read as H<heavy weight>L<light weight>, where the light weight is
# the one given to the hydrogens, so HL1:0 leaves the hydrogens out of the RMSD and
# HL1:1 weighs every atom the same.
HEAVY_ATOMS_ONLY_WEIGHTS_VECTOR = "HL1:0"
ALL_ATOMS_WEIGHTS_VECTOR = "HL1:1"

# the ways the sampler can rotate a geometry onto the seed geometry: KU is Kabsch-Umeyama
# and R is the rotation scipy aligns the two sets of coordinates with
ROTATION_METHODS = ["KU", "R"]

# The memory the sampler needs is worked out from what polus' DIVSampler.SetRMSDMatrix
# actually allocates. It is in the parent process (the pool workers only read), so what
# has to fit is the memory of the whole job, i.e. all of the cores it asks for.
#
# The RMSD matrix is held as an ngeoms x ngeoms array of float32 for the whole run, no
# matter how the work is chunked, so it grows with the square of the trajectory length
# and is what makes a long trajectory impossible to sample rather than merely slow.
BYTES_PER_MATRIX_ELEMENT = 4
# On top of that, each batch builds a block of chunk_size x ngeoms elements three times
# over: a python int in the list of indices handed to the process pool (~44 bytes each
# once the over-allocation of the list holding them is counted), a python float in the
# list of results it gives back (~33 bytes), and a float32 in the temporary matrix they
# are copied into (4). The index list is still alive while the results are collected, so
# they add up rather than taking turns. These are measured numbers: a batch of
# 100,020,001 elements was seen to take 4.5 GB for the index list alone.
BYTES_PER_CHUNK_ELEMENT = 44 + 33 + 4
# The largest number of elements a batch is allowed to cover, whatever the memory of the
# job. The lists above are made of individual python objects, so a batch big enough to
# cover the whole matrix at once builds a list of hundreds of millions of them, which the
# process pool then has to pickle (and fork around) in one go. Keeping a batch to this
# many elements keeps that under about a GB and costs only the time of starting a few
# more pools.
MAXIMUM_CHUNK_ELEMENTS = 10_000_000
# The fraction of the job's memory the estimate is allowed to take. The rest covers the
# things which are not worth modelling: the lines of the .xyz file, the geometries as
# python lists and as rotated arrays, the pickled copies of the batch that the process
# pool hands to its workers (and the pages of the parent they touch after forking), and
# the interpreter itself.
MEMORY_FRACTION = 0.35
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
    """Returns the memory (in GB) that one core is given on this machine."""

    return get_param_from_config(
        ichor.hpc.global_variables.ICHOR_CONFIG,
        ichor.hpc.global_variables.MACHINE,
        "hpc",
        "memory_per_core_gb",
        default=FALLBACK_MEMORY_PER_CORE_GB,
    )


def job_memory_gb(ncores: int) -> float:
    """Returns the memory (in GB) a job asking for the given number of cores can use, as
    the batch system hands out memory per core. Asking for more cores is therefore how a
    longer trajectory (or a larger chunk) is given the memory it needs."""

    return ncores * memory_per_core_gb()


def memory_budget_gb(ncores: int) -> float:
    """Returns the memory (in GB) the estimate is allowed to account for, which is the
    part of the job's memory left over once the things which are not modelled (see
    :data:`MEMORY_FRACTION`) are allowed for."""

    return MEMORY_FRACTION * job_memory_gb(ncores)


def process_copies(ncores: int) -> int:
    """Returns how many times over the sampler's memory is counted against the job.

    Each batch is worked out by a pool of ``ncores`` worker processes, which the sampler
    forks once it is already holding the RMSD matrix and the indices of the batch. Every
    one of them inherits all of that, and the pages show up in each of their resident
    sizes, so what the batch system sees is the sampler's memory once per worker as well
    as once for the sampler itself.

    A job of 10,001 geometries was killed for using 81.6 GB of its 32 GB while the
    sampler itself was holding 4.94 GB: 4.94 x (1 + 16 workers) = 84 GB. The 16 was
    polus' default pool size, which is why the number of cores is now passed to it.

    :param ncores: The number of cores the job asks for, which is the size of the pool.
    """

    return 1 + ncores


def per_process_budget_gb(ncores: int) -> float:
    """Returns the memory (in GB) the sampler itself is allowed to hold.

    As the job's memory grows with the cores it asks for but its memory is counted once
    per worker (see :func:`process_copies`), the two nearly cancel: what one process may
    hold works out at little more than the memory of a single core however many cores are
    asked for. This is the number which decides whether a trajectory can be sampled.
    """

    return memory_budget_gb(ncores) / process_copies(ncores)


def peak_memory_gb(chunk_size: int, ngeometries: int, ncores: int) -> float:
    """Returns the memory (in GB) the job is estimated to be charged for in total, i.e.
    what the sampler holds counted once per process (see :func:`process_copies`)."""

    return process_copies(ncores) * total_memory_gb(chunk_size, ngeometries)


def rmsd_matrix_memory_gb(ngeometries: int) -> float:
    """Returns the memory (in GB) taken by the RMSD matrix of every geometry against
    every other one, which the sampler holds for the whole run.

    :param ngeometries: The number of geometries in the trajectory.
    """

    return ngeometries**2 * BYTES_PER_MATRIX_ELEMENT / 1024**3


def chunk_memory_gb(chunk_size: int, ngeometries: int) -> float:
    """Returns the memory (in GB) taken by one batch of the sampler on top of the RMSD
    matrix (see :data:`BYTES_PER_CHUNK_ELEMENT`).

    :param chunk_size: The number of geometries whose RMSDs are computed at a time.
    :param ngeometries: The number of geometries in the trajectory.
    """

    return chunk_size * ngeometries * BYTES_PER_CHUNK_ELEMENT / 1024**3


def total_memory_gb(chunk_size: int, ngeometries: int) -> float:
    """Returns the memory (in GB) the sampling job is estimated to need in total."""

    return rmsd_matrix_memory_gb(ngeometries) + chunk_memory_gb(chunk_size, ngeometries)


def format_memory_gb(memory_gb: float) -> str:
    """Formats a memory estimate for display, e.g. ``about 1.5 GB``. An estimate too
    small to show is worded as such rather than being shown as the 0.0 GB it would round
    to, so the qualifier is part of what is returned."""

    if memory_gb < 0.05:
        return "less than 0.1 GB"

    return f"about {memory_gb:,.1f} GB"


def largest_trajectory_for(ncores: int) -> int:
    """Returns the longest trajectory whose RMSD matrix alone fits in what one process is
    allowed to hold, which is the hard limit on what can be sampled at all (a chunk of any
    size needs room on top of it).

    Asking for more cores barely moves this, as the memory they bring is also counted
    once per worker (see :func:`per_process_budget_gb`), so a trajectory which does not
    fit has to be thinned rather than given a larger job.

    :param ncores: The number of cores the job asks for.
    """

    budget_bytes = per_process_budget_gb(ncores) * 1024**3

    return int((budget_bytes / BYTES_PER_MATRIX_ELEMENT) ** 0.5)


def maximum_cores() -> int:
    """Returns the largest number of cores a job can ask for on this machine, taken from
    the parallel environments it has. 0 means the machine (or its parallel environments)
    is not in the config, so there is no limit to check against."""

    environments = get_param_from_config(
        ichor.hpc.global_variables.ICHOR_CONFIG,
        ichor.hpc.global_variables.MACHINE,
        "hpc",
        "parallel_environments",
        default=None,
    )
    if not environments:
        return 0

    # each environment is a [smallest, largest] number of cores it can be used for
    return max(int(bounds[1]) for bounds in environments.values())


def capped_chunk_size(ngeometries: int) -> int:
    """Returns the largest chunk size which keeps a batch within
    :data:`MAXIMUM_CHUNK_ELEMENTS`, which is the ceiling every suggestion is held under
    however much memory the job has.

    :param ngeometries: The number of geometries in the trajectory.
    """

    return max(1, min(ngeometries, MAXIMUM_CHUNK_ELEMENTS // ngeometries))


def cores_needed_for(
    ngeometries: int, chunk_size: int = MINIMUM_SUGGESTED_CHUNK_SIZE
) -> int:
    """Returns the number of cores whose memory would hold the RMSD matrix of the given
    trajectory, plus a chunk of the given size.

    The cores have to cover what one process holds once for every worker as well as for
    the sampler itself, so ``(1 + n)`` lots of it have to fit in ``n`` cores' worth of
    memory. Solving that for ``n`` leaves a ceiling: once one process needs more than the
    memory of a single core, no number of cores is enough.

    :param ngeometries: The number of geometries in the trajectory.
    :param chunk_size: The number of geometries whose RMSDs are computed at a time. The
        default is the smallest chunk worth using, which gives the smallest job the
        trajectory can be sampled by at all.
    :return: The number of cores needed, or 0 if no number of them would be enough.
    """

    needed_gb = total_memory_gb(chunk_size, ngeometries)
    per_core_gb = MEMORY_FRACTION * memory_per_core_gb()

    # (1 + n) * needed <= n * per_core  ->  n >= needed / (per_core - needed)
    if needed_gb >= per_core_gb:
        return 0

    return max(1, math.ceil(needed_gb / (per_core_gb - needed_gb)))


def suggest_number_of_cores(ngeometries: int) -> int:
    """Returns the number of cores to ask for, which is the number the memory of the job
    has to come from (see :func:`cores_needed_for`).

    A chunk size the user has pinned is taken as given and the cores are made to fit
    around it. Otherwise the chunk size is the one which follows the cores, and as it is
    held under a ceiling of its own (see :func:`capped_chunk_size`) what a batch can cost
    is bounded, so the cores only have to cover the RMSD matrix and one of those.

    :param ngeometries: The number of geometries in the trajectory. If this is not known
        (0), the menu default is returned instead.
    """

    if ngeometries <= 0:
        return SUBMIT_DIVERSITY_MENU_DEFAULTS["default_ncores"]

    if chunk_size_overridden:
        return cores_needed_for(
            ngeometries, submit_diversity_menu_options.selected_chunk_size
        )

    return cores_needed_for(ngeometries, capped_chunk_size(ngeometries))


def suggest_chunk_size(ngeometries: int, ncores: int) -> int:
    """Returns a chunk size which, on top of the RMSD matrix the trajectory needs, fits
    in the memory of a job asking for the given number of cores.

    :param ngeometries: The number of geometries in the trajectory. If this is not known
        (0), the menu default is returned instead.
    :param ncores: The number of cores the job asks for.
    """

    if ngeometries <= 0:
        return SUBMIT_DIVERSITY_MENU_DEFAULTS["default_chunk_size"]

    remaining_gb = per_process_budget_gb(ncores) - rmsd_matrix_memory_gb(ngeometries)
    # the trajectory is too long to sample with this many cores whatever the chunk size,
    # which the menu checks warn about; the smallest useful chunk is the best on offer
    if remaining_gb <= 0:
        return MINIMUM_SUGGESTED_CHUNK_SIZE

    chunk_size = int(remaining_gb * 1024**3 // (ngeometries * BYTES_PER_CHUNK_ELEMENT))
    # a job with memory to spare must still not be given a batch which covers the whole
    # matrix in one go (see :data:`MAXIMUM_CHUNK_ELEMENTS`)
    chunk_size = min(chunk_size, capped_chunk_size(ngeometries))

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

    def check_trajectory_fits_in_memory(self) -> Union[str, None]:
        """Checks that the RMSD matrix of the trajectory fits in the memory of the job.

        The sampler compares every geometry against every other one and keeps the whole
        matrix, so the memory it needs grows with the square of the length of the
        trajectory and no chunk size can make a trajectory which does not fit fit."""
        ngeometries = self.number_of_geometries_in_file
        # a job with no cores has no memory to fit anything in, but that is the number of
        # cores being wrong rather than the trajectory, which the check above says
        if not ngeometries or self.selected_number_of_cores < 1:
            return None

        ncores = self.selected_number_of_cores
        matrix_gb = rmsd_matrix_memory_gb(ngeometries)
        if matrix_gb <= per_process_budget_gb(ncores):
            return None

        needed_cores = cores_needed_for(ngeometries)
        largest_cores = maximum_cores()
        # the memory more cores bring is also counted once per worker, so they are only
        # a way out of this while one process still fits in a single core's memory
        if not needed_cores:
            way_out = (
                "No number of cores would fit it, as the memory they bring is counted "
                "once for every worker as well, so the trajectory has to be thinned to "
                f"about {largest_trajectory_for(ncores):,} geometries or fewer."
            )
        elif largest_cores and needed_cores > largest_cores:
            way_out = (
                f"That would need {needed_cores:,} cores, more than the "
                f"{largest_cores:,} a job can ask for on this machine, so the "
                f"trajectory has to be thinned to about "
                f"{largest_trajectory_for(largest_cores):,} geometries or fewer."
            )
        else:
            way_out = (
                f"Thin the trajectory to about {largest_trajectory_for(ncores):,} "
                f"geometries or ask for {needed_cores:,} cores."
            )

        return (
            f"The {ngeometries:,} geometries in the trajectory need a {matrix_gb:,.1f} "
            f"GB RMSD matrix, and the sampler is charged for it once per worker, so a "
            f"{ncores} core job may hold only about "
            f"{per_process_budget_gb(ncores):,.1f} GB of it. {way_out}"
        )

    def check_number_of_cores_fits_machine(self) -> Union[str, None]:
        """Checks the job does not ask for more cores than the machine can give it."""
        largest = maximum_cores()
        if largest and self.selected_number_of_cores > largest:
            return (
                f"Current number of cores: {self.selected_number_of_cores:,} is more "
                f"than the {largest:,} a job can ask for on this machine."
            )

    def check_selected_chunk_size(self) -> Union[str, None]:
        """Checks the chunk size is positive, is not larger than the trajectory, and
        that what it needs on top of the RMSD matrix fits in the memory of the job."""
        if self.selected_chunk_size < 1:
            return (
                f"Current chunk size: {self.selected_chunk_size} must be 1 or greater."
            )

        ngeometries = self.number_of_geometries_in_file
        if not ngeometries:
            return None

        if self.selected_chunk_size > ngeometries:
            return (
                f"Current chunk size: {self.selected_chunk_size:,} is larger than the "
                f"{ngeometries:,} geometries in the trajectory."
            )

        ncores = self.selected_number_of_cores
        budget_gb = per_process_budget_gb(ncores)
        # a trajectory whose matrix alone does not fit is reported by the check above,
        # which says what to do about it; no chunk size would save it
        if rmsd_matrix_memory_gb(ngeometries) > budget_gb:
            return None

        # the lists a batch is made of are python objects rather than an array, so a
        # batch covering too much of the matrix at once is worth warning about on its own
        # (a job with memory to spare is still killed building and pickling them)
        if self.selected_chunk_size * ngeometries > MAXIMUM_CHUNK_ELEMENTS:
            return (
                f"Current chunk size: {self.selected_chunk_size:,} makes each batch "
                f"cover {self.selected_chunk_size * ngeometries:,} elements of the RMSD "
                f"matrix, which the sampler builds a python list of before it starts "
                f"working them out. Keep it under "
                f"{MAXIMUM_CHUNK_ELEMENTS // ngeometries:,} (a chunk size of "
                f"{suggest_chunk_size(ngeometries, self.selected_number_of_cores):,} "
                f"would do), or the job is likely to be killed for running out of "
                f"memory before the first batch has begun."
            )

        needed_gb = total_memory_gb(self.selected_chunk_size, ngeometries)
        if needed_gb > budget_gb:
            return (
                f"Current chunk size: {self.selected_chunk_size:,} brings what the "
                f"sampler holds to about {needed_gb:,.1f} GB, which is charged once for "
                f"the sampler and once per worker, so a {ncores} core job would be "
                f"asked for about {peak_memory_gb(self.selected_chunk_size, ngeometries, ncores):,.1f} GB "  # noqa: E501
                f"of its {job_memory_gb(ncores):,.0f} GB and may be killed for running "
                f"out of memory. A chunk size of "
                f"{suggest_chunk_size(ngeometries, ncores):,} would fit."
            )

    def check_selected_rotation_method(self) -> Union[str, None]:
        """Checks that the rotation method is one the sampler knows about."""
        if self.selected_rotation_method not in ROTATION_METHODS:
            return (
                f"Current rotation method: {self.selected_rotation_method} is not one "
                f"of {', '.join(ROTATION_METHODS)}."
            )


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

# the chunk size follows the length of the trajectory and the memory of the job unless
# the user picks one by hand, in which case their choice is kept even when a different
# trajectory (or number of cores) is selected
chunk_size_overridden = False


def derive_chunk_size():
    """Sets the chunk size from the length of the selected trajectory and the memory the
    job asks for, unless the user has picked one by hand. Both of those can change while
    the menu is open, which is why this is done in one place."""

    if chunk_size_overridden:
        return

    submit_diversity_menu_options.selected_chunk_size = suggest_chunk_size(
        submit_diversity_menu_options.number_of_geometries_in_file,
        submit_diversity_menu_options.selected_number_of_cores,
    )


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
    derive_chunk_size()

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
        """Asks user to select the number of cores, which the RMSDs are computed in
        parallel over. As the batch system hands out memory per core, this is also how
        much memory the job has to hold the RMSD matrix and its chunks in, so the chunk
        size is derived again from it (unless it was picked by hand).

        The number of cores the trajectory needs to fit at all is suggested (see
        :func:`suggest_number_of_cores`); entering 0 asks for that many."""
        ngeometries = submit_diversity_menu_options.number_of_geometries_in_file
        suggested = suggest_number_of_cores(ngeometries)

        if ngeometries and not suggested:
            print(
                f"The {ngeometries:,} geometries in the trajectory need "
                f"{format_memory_gb(rmsd_matrix_memory_gb(ngeometries))} for their RMSD "
                f"matrix, which no number of cores would fit: the sampler is charged "
                f"for what it holds once per worker as well, so asking for more cores "
                f"brings little more than one core's {memory_per_core_gb()} GB with it. "
                f"Thin the trajectory in the sampling menu above this one."
            )
        elif ngeometries:
            largest = maximum_cores()
            print(
                f"The {ngeometries:,} geometries in the trajectory need at least "
                f"{suggested:,} cores, as their RMSD matrix takes "
                f"{format_memory_gb(rmsd_matrix_memory_gb(ngeometries))} and it is "
                f"charged once for the sampler and once per worker against the "
                f"{memory_per_core_gb()} GB each core brings. More cores than that also "
                f"work out the RMSDs faster."
            )
            if largest and suggested > largest:
                print(
                    f"Note that this is more than the {largest:,} cores a job can ask "
                    f"for on this machine, so the trajectory has to be thinned instead "
                    f"(the sampling menu above this one can do that)."
                )

        ncores = user_input_int(
            "Enter number of cores (0 = the number the trajectory needs): ",
            submit_diversity_menu_options.selected_number_of_cores,
            minimum=0,
        )
        submit_diversity_menu_options.selected_number_of_cores = (
            ncores
            or suggested
            or submit_diversity_menu_options.selected_number_of_cores
        )
        derive_chunk_size()

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
        """Asks user to select the chunk size, i.e. how many geometries have their RMSDs
        computed in one batch. It is what the memory the job needs on top of the RMSD
        matrix is set by (see :func:`chunk_memory_gb`), so too large a chunk gets the job
        killed and too small a chunk makes it slow.

        The chunk size is derived from the length of the trajectory and the memory the
        job asks for (see :func:`suggest_chunk_size`) unless it is given here, in which
        case the given value is kept even when a different trajectory or number of cores
        is selected. Entering 0 goes back to deriving it."""
        global chunk_size_overridden

        ngeometries = submit_diversity_menu_options.number_of_geometries_in_file
        ncores = submit_diversity_menu_options.selected_number_of_cores
        suggested = suggest_chunk_size(ngeometries, ncores)

        if ngeometries:
            print(
                f"Suggested chunk size for the {ngeometries:,} geometries in the "
                f"trajectory: {suggested:,} ("
                f"{format_memory_gb(total_memory_gb(suggested, ngeometries))} in total, "
                f"of the {job_memory_gb(ncores):,.0f} GB a {ncores} core job is given, "
                f"with {format_memory_gb(rmsd_matrix_memory_gb(ngeometries))} of it "
                f"taken by the RMSD matrix whatever the chunk size)"
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
        """Asks for the method used to rotate the geometries onto the seed geometry:
        KU (Kabsch-Umeyama, the default) or R (the rotation scipy aligns the two sets of
        coordinates with)."""
        submit_diversity_menu_options.selected_rotation_method = user_input_restricted(
            ROTATION_METHODS,
            "Select rotation method: ",
            submit_diversity_menu_options.selected_rotation_method,
        ).upper()

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
        elif ngeometries and rmsd_matrix_memory_gb(ngeometries) > per_process_budget_gb(
            ncores
        ):
            problem = (
                f"The {ngeometries:,} geometries in the trajectory need a "
                f"{rmsd_matrix_memory_gb(ngeometries):,.1f} GB RMSD matrix, and it is "
                f"charged once for the sampler and once per worker, so a {ncores} core "
                f"job can hold only about {per_process_budget_gb(ncores):,.1f} GB of it."
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
                    "The sampler compares every geometry against every other one and "
                    "keeps the whole RMSD matrix in memory, so the memory it needs grows "
                    "with the square of the length of the trajectory. A trajectory which "
                    "does not fit has to be thinned (e.g. take every nth step of it) or "
                    "be given a job with more cores, as no chunk size will save it.",
                ],
            )
            return

        # the RMSDs are computed by a pool of worker processes, so it is only worth
        # asking for that when the job has more than the one core to run them on. Note
        # that the sampler goes through the pool anyway for a trajectory of more than
        # 1000 geometries, which is why the number of cores is what matters most here.
        parallel = ncores > 1

        div_script = write_diversity_sampling(
            filename=trajectory_path,
            seed_geom=xyz_path,
            weights_vector=weights_vector(),
            sample_size=sample_sizes,
            chunk_size=chunk_size,
            # without this the sampler starts its own default number of processes
            # (16), which has nothing to do with the cores the job asked for
            ncores=ncores,
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
                "RMSD matrix": (
                    f"{format_memory_gb(rmsd_matrix_memory_gb(ngeometries))} "
                    f"({ngeometries:,} x {ngeometries:,} geometries)"
                    if ngeometries
                    else "not known (the trajectory could not be counted)"
                ),
                "Estimated memory": (
                    f"{format_memory_gb(total_memory_gb(chunk_size, ngeometries))} "
                    f"held by the sampler, charged as "
                    f"{format_memory_gb(peak_memory_gb(chunk_size, ngeometries, ncores))}"
                    f" over its {process_copies(ncores)} processes, of the "
                    f"{job_memory_gb(ncores):,.0f} GB this job is given"
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
                "The sampler compares every geometry against every other one and holds "
                "the whole RMSD matrix, so most of the memory above is set by the "
                "length of the trajectory rather than by the chunk size, and it grows "
                "with the square of it. The chunk size only sets how much of that "
                "matrix is worked out at a time, so a smaller chunk uses less memory on "
                "top of it but takes longer.",
                "The RMSDs are worked out by a pool of one worker process per core, "
                "each of which is forked once the sampler already holds the matrix and "
                "the batch, so what it holds is charged against the job once per worker "
                "as well. Asking for more cores therefore brings little more memory "
                "than it takes: a trajectory which does not fit has to be thinned "
                "rather than given a larger job.",
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
