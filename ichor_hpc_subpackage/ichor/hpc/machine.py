import os
from enum import auto
from pathlib import Path
from typing import Optional

from ichor.core.common.functools import cached_property
from ichor.core.common.io import mkdir, move
from ichor.core.common.types import Enum
from ichor.hpc.uid import get_uid


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
        if self.submit_on_compute:
            submit_type = SubmitType.SubmitOnCompute
        elif self.drop_compute_available:
            from ichor.hpc.drop_compute import get_drop_compute

            if get_drop_compute(self).is_available_to_user:
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


def get_machine_from_file(machine_file: Optional[Path] = None) -> Machine:
    from ichor.hpc import FILE_STRUCTURE

    if machine_file is None:
        machine_file = FILE_STRUCTURE["machine"]

    if machine_file.exists():
        with open(machine_file, "r") as f:
            _machine = f.read().strip()
            if _machine:
                if _machine not in Machine.names:
                    raise MachineNotFound(
                        f"Unknown machine '{_machine}' in '{FILE_STRUCTURE['machine']}'"
                    )
                else:
                    return Machine.from_name(_machine)


def init_machine(machine_name: str, machine_file: Optional[Path] = None) -> Machine:
    machine = get_machine_from_name(machine_name)

    if machine_file is None:
        from ichor.hpc import FILE_STRUCTURE

        machine_file = FILE_STRUCTURE["machine"]

    if machine is Machine.local and machine_file.exists():
        machine = get_machine_from_file(machine_file)

    # if machine has been successfully identified, write to FILE_STRUCTURE['machine']
    if machine is not Machine.local and (
        not machine_file.exists()
        or machine_file.exists()
        and get_machine_from_file() != machine
    ):
        mkdir(machine_file.parent)
        machine_filepart = Path(str(machine_file) + f".{get_uid()}.filepart")
        with open(machine_filepart, "w") as f:
            f.write(f"{machine.name}")
        move(machine_filepart, machine_file)

    return machine
