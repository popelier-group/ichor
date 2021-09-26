from enum import Enum
from typing import Any, Callable, Optional, Sequence

from ichor.auto_run.auto_run_aimall import submit_aimall_job_to_auto_run
from ichor.auto_run.auto_run_ferebus import submit_ferebus_job_to_auto_run
from ichor.auto_run.auto_run_gaussian import submit_gaussian_job_to_auto_run
from ichor.auto_run.ichor import (make_models,
                                  submit_ichor_active_learning_job_to_auto_run,
                                  submit_ichor_aimall_command_to_auto_run,
                                  submit_ichor_gaussian_command_to_auto_run,
                                  submit_make_sets_job_to_auto_run)
from ichor.batch_system import JobID
from ichor.common.int import truncate
from ichor.common.io import mkdir
from ichor.common.points import get_points_location
from ichor.common.types import MutableValue
from ichor.drop_compute import DROP_COMPUTE_LOCATION
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import Trajectory
from ichor.machine import MACHINE, SubmitType
from ichor.make_sets import make_sets_npoints
from ichor.points import PointsDirectory
from ichor.submission_script import SCRIPT_NAMES, DataLock

__all__ = [
    "submit_gaussian_job_to_auto_run",
    "submit_aimall_job_to_auto_run",
    "submit_ferebus_job_to_auto_run",
    "submit_ichor_gaussian_command_to_auto_run",
    "submit_ichor_aimall_command_to_auto_run",
    "make_models",
    "submit_ichor_active_learning_job_to_auto_run",
    "auto_run",
]