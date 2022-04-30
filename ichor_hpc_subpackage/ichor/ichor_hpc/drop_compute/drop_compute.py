from pathlib import Path

from ichor.ichor_lib.common.os import current_user_groups
from ichor.ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_hpc.machine_setup.machine.machine import MACHINE, Machine

DROP_COMPUTE_TMP_LOCATION: Path = FILE_STRUCTURE["tmp"]
DROP_COMPUTE_LOCATION: Path = FILE_STRUCTURE[
    "scripts"
]  # should be overwritten
DROP_COMPUTE_GROUP: str = "dropcompute"

DROP_COMPUTE_MAX_JOBS = 150

DROP_COMPUTE_NTRIES = 1000

if MACHINE is Machine.csf3:
    DROP_COMPUTE_LOCATION = Path.home() / Path("scratch") / Path("DropCompute")
    DROP_COMPUTE_GROUP = "ri_dropcompute"


def drop_compute_available_for_user() -> bool:
    return DROP_COMPUTE_GROUP in current_user_groups()
