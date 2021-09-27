from enum import Enum
from typing import Any, Callable, Optional, Sequence

from ichor.auto_run.auto_run_aimall import submit_aimall_job_to_auto_run
from ichor.auto_run.auto_run_ferebus import submit_ferebus_job_to_auto_run
from ichor.auto_run.auto_run_gaussian import submit_gaussian_job_to_auto_run
from ichor.auto_run.ichor_jobs import (make_models,
                                  submit_ichor_active_learning_job_to_auto_run,
                                  submit_ichor_aimall_command_to_auto_run,
                                  submit_ichor_gaussian_command_to_auto_run,
                                  submit_make_sets_job_to_auto_run)

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