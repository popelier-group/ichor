from ichor.machine import MACHINE, Machine
from pathlib import Path
import os
import grp
from ichor.file_structure import FILE_STRUCTURE
from ichor.common.os import current_user_groups


DROP_COMPUTE_LOCATION: Path = FILE_STRUCTURE["scripts"]  # should be overwritten
DROP_COMPUTE_GROUP: str = "dropcompute"

if MACHINE is Machine.csf3:
    DROP_COMPUTE_LOCATION = Path.home() / Path("scratch") / Path("DropCompute")
    DROP_COMPUTE_GROUP = "ri_dropcompute"


def drop_compute_available_for_user() -> bool:
    # todo: implement check for if drop-n-compute is available to the current user
    return DROP_COMPUTE_GROUP in current_user_groups()
