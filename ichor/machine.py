import platform
from enum import auto

from ichor.common.types import Enum
from ichor.file_structure import FILE_STRUCTURE


class MachineNotFound(Exception):
    pass


class SubmitType(Enum):
    """Enum holding information on various submission systems ichor implements"""

    HoldQueueWait = auto()
    SubmitOnCompute = auto()
    DropCompute = auto()


class Machine(Enum):
    """Enum which is used to define any machines that ICHOR is running on. This needs to be done because commands and settings change between different machines."""

    csf3 = "csf3.itservices.manchester.ac.uk", False, True
    ffluxlab = "ffluxlab.mib.manchester.ac.uk", True, False
    local = "local", False, False

    def __init__(
        self,
        address: str,
        submit_on_compute: bool,
        drop_n_compute_available: bool,
    ):
        self.address = address

        self.submit_type = SubmitType.HoldQueueWait
        if submit_on_compute:
            self.submit_type = SubmitType.SubmitOnCompute
        elif drop_n_compute_available:
            if drop_n_compute_available_for_user():
                self.submit_type = SubmitType.DropCompute


def drop_n_compute_available_for_user() -> bool:
    # todo: implement check for if drop-n-compute is available to the current user
    return True


machine_name = platform.node()

MACHINE = Machine.local
if "csf3." in machine_name:
    MACHINE = Machine.csf3
elif "ffluxlab" in machine_name:
    MACHINE = Machine.ffluxlab

# if machine hasn't been identified, check whether the machine has been saved to FILE_STRUCTURE['machine']
if MACHINE is Machine.local:
    if FILE_STRUCTURE["machine"].exists():
        with open(FILE_STRUCTURE["machine"], "r") as f:
            _machine = f.read()
            if _machine not in Machine.names:
                raise MachineNotFound(
                    f"Unknown machine ({_machine}) in {FILE_STRUCTURE['machine']}"
                )
            MACHINE = Machine.from_name(_machine)

# if machine has been successfully identified, write to FILE_STRUCTURE['machine']
if MACHINE is not Machine.local:
    with open(FILE_STRUCTURE["machine"], "w") as f:
        f.write(f"{MACHINE.name}")
