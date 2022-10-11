from pathlib import Path
from typing import Optional

from ichor.core.common.os import current_user_groups
from ichor.hpc import FILE_STRUCTURE
from ichor.core.common.io import mkdir


# todo: not sure this is the best use of a class, need to do research
class DropCompute:
    """Drop Compute is only available on CSF3 currently. If this changes, this class
    will be need updating."""

    TMP_LOCATION = FILE_STRUCTURE["tmp"]

    def __init__(
        self,
        unix_group: str,
        max_jobs: int,
        ntries: Optional[int] = None,
        location: Optional[Path] = None,
    ):
        self._unix_group: str = unix_group
        self.max_jobs = max_jobs
        self.ntries = ntries or 1000
        self.location = location or ""

        if self.location is None:
            raise ValueError(
                f"Must define 'location' attribute of '{self.__class__.__name__}' instance, cannot be 'None'"
            )
        elif self.location.exists() and not self.location.is_dir():
            raise ValueError(
                f"'location' attribute of '{self.__class__.__name__}' instance must be a directory"
            )
        elif not self.location.exists():
            mkdir(self.location)

    @property
    def is_available_to_user(self) -> bool:
        """Returns True if the user belongs to the drop compute group on CSF3 or False
        if the user does not belong to the drop compute group on CSF3."""
        return self._unix_group in current_user_groups()


def get_drop_compute(
    machine: Optional["Machine"] = None,
) -> Optional[DropCompute]:
    from ichor.hpc import MACHINE
    from ichor.hpc.machine import Machine

    machine = machine or MACHINE

    if machine in {Machine.csf3, Machine.csf4}:
        return DropCompute(
            unix_group="ri_dropcompute",
            location=Path.home() / Path("scratch") / Path("DropCompute"),
            max_jobs=150,
        )
