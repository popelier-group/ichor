import os
import platform
from enum import auto
from pathlib import Path

from ichor.ichor_lib.common.functools import cached_property
from ichor.ichor_lib.common.io import mkdir, move
from ichor.ichor_lib.common.types import Enum
from ichor.ichor_lib.common.uid import get_uid
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE


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

    csf3 = "csf3.itservices.manchester.ac.uk", False, True
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
            from ichor_hpc.drop_compute.drop_compute import drop_compute_available_for_user

            if drop_compute_available_for_user():
                submit_type = SubmitType.DropCompute

        return submit_type


def _try_get_machine_from_file():
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


machine_name = platform.node()

MACHINE = Machine.local
if "csf3." in machine_name:
    MACHINE = Machine.csf3
elif "ffluxlab" in machine_name:
    MACHINE = Machine.ffluxlab

# if machine hasn't been identified, check whether the machine has been saved to FILE_STRUCTURE['machine']
if MACHINE is Machine.local:
    _machine = _try_get_machine_from_file()
    if _machine is not None:
        MACHINE = _machine

if MACHINE is Machine.local:
    from ichor.batch_system import BATCH_SYSTEM

    if BATCH_SYSTEM.Host in os.environ.keys():
        host = os.environ[BATCH_SYSTEM.Host]
        if host == "ffluxlab":
            MACHINE = Machine.ffluxlab

# if machine has been successfully identified, write to FILE_STRUCTURE['machine']
if MACHINE is not Machine.local and (
    not FILE_STRUCTURE["machine"].exists()
    or (
        FILE_STRUCTURE["machine"].exists()
        and not _try_get_machine_from_file() is None
    )
):
    mkdir(FILE_STRUCTURE["machine"].parent)
    machine_filepart = Path(
        str(FILE_STRUCTURE["machine"]) + f".{get_uid()}.filepart"
    )
    with open(machine_filepart, "w") as f:
        f.write(f"{MACHINE.name}")
    move(machine_filepart, FILE_STRUCTURE["machine"])
