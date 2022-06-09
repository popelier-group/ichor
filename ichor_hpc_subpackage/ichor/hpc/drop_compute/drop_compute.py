from pathlib import Path

from ichor.core.common.os import current_user_groups
from ichor.hpc import FILE_STRUCTURE


# todo: not sure this is the best use of a class, need to do research
class DropCompute:
    """Drop Compute is only available on CSF3 currently. If this changes, this class
    will be need updating."""

    TMP_LOCATION = FILE_STRUCTURE["tmp"]
    LOCATION: Path = Path.home() / Path("scratch") / Path("DropCompute")
    GROUP: str = "ri_dropcompute"
    MAX_JOBS = 150
    NTRIES = 1000


def drop_compute_available_for_user() -> bool:
    """Returns True if the user belongs to the drop compute group on CSF3 or False
    if the user does not belong to the drop compute group on CSF3."""
    return DropCompute.GROUP in current_user_groups()
