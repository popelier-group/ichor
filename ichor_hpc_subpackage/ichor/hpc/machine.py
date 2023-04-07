from enum import auto

from ichor.core.common.functools import cached_property
from ichor.core.common.types import Enum


class MachineNotFound(Exception):
    pass


class SubmitType(Enum):
    """Enum holding information on various submission systems ichor implements"""

    HoldQueueWait = auto(), False
    SubmitOnCompute = auto(), True
    DropCompute = auto(), True

    def __init__(self, id_: int, submit_after_final_step: bool):
        self._id = id_
        self.submit_after_final_step = submit_after_final_step


class Machine(Enum):
    """Enum which is used to define any machines that ICHOR is running on.
    This needs to be done because commands and settings change between different machines."""

    # Machine Name = Machine Address, Can Submit on Compute, DropCompute available
    csf3 = "csf3.itservices.manchester.ac.uk", False, True
    csf4 = "csf4.itservices.manchester.ac.uk", False, True
    ffluxlab = "ffluxlab.mib.manchester.ac.uk", True, False
    local = "local", False, False

    def __init__(
        self,
        address: str,
        submit_on_compute: bool,
        drop_compute_available: bool,
    ):
        self.address = address
        self.submit_on_compute = submit_on_compute
        self.drop_compute_available = drop_compute_available

    @cached_property
    def submit_type(self) -> SubmitType:
        submit_type = SubmitType.HoldQueueWait
        # if self.submit_on_compute:
        #     submit_type = SubmitType.SubmitOnCompute
        # elif self.drop_compute_available:
        #     from ichor.hpc.drop_compute import get_drop_compute

        #     if get_drop_compute(self).is_available_to_user:
        #         submit_type = SubmitType.DropCompute

        return submit_type
