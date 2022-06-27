import os
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
    """Enum which is used to define any machines that ICHOR is running on. This needs to be done because commands and settings change between different machines."""

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
        if self.submit_on_compute:
            submit_type = SubmitType.SubmitOnCompute
        elif self.drop_compute_available:
            from ichor.hpc.drop_compute.drop_compute import (
                drop_compute_available_for_user,
            )

            if drop_compute_available_for_user():
                submit_type = SubmitType.DropCompute

        return submit_type


def get_machine_from_name(platform_name: str):
    from ichor.hpc import BATCH_SYSTEM

    m = Machine.local
    if "csf3." in platform_name:
        m = Machine.csf3
    elif "csf4." in platform_name:
        m = Machine.csf4
    elif "ffluxlab" in platform_name:
        m = Machine.ffluxlab

    if BATCH_SYSTEM.Host in os.environ.keys():
        host = os.environ[BATCH_SYSTEM.Host]
        if host == "ffluxlab":
            m = Machine.ffluxlab

    return m


def get_machine_from_file():
    from ichor.hpc import FILE_STRUCTURE

    if FILE_STRUCTURE["machine"].exists():
        with open(FILE_STRUCTURE["machine"], "r") as f:
            _machine = f.read().strip()
            if _machine:
                if _machine not in Machine.names:
                    raise MachineNotFound(
                        f"Unknown machine '{_machine}' in '{FILE_STRUCTURE['machine']}'"
                    )
                else:
                    return Machine.from_name(_machine)
