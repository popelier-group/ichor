"""What a job can be given on the machine ichor is running on.

The batch system hands out memory per core, so the number of cores a job asks for is what
sets how much memory it has, whether or not it has any use for the cores themselves. Any
menu which sizes a job around the memory it needs therefore has to know how much memory a
core brings on this machine and how many cores a job may ask for, both of which are read
from the ichor config.
"""

import ichor.hpc.global_variables
from ichor.hpc.global_variables import get_param_from_config

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
    job which needs more memory is given it, even when it has no use for the cores."""

    return ncores * memory_per_core_gb()


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


def format_memory_gb(memory_gb: float) -> str:
    """Formats a memory estimate for display, e.g. ``about 1.5 GB``. An estimate too
    small to show is worded as such rather than being shown as the 0.0 GB it would round
    to, so the qualifier is part of what is returned."""

    if memory_gb < 0.05:
        return "less than 0.1 GB"

    return f"about {memory_gb:,.1f} GB"
