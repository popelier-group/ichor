from pathlib import Path
from typing import List, Optional, Union

from ichor.batch_system import JobID
from ichor.common.types import MutableValue
from ichor.submission_script import (
    SCRIPT_NAMES,
    ICHORCommand,
    SubmissionScript,
    TimingManager,
)


def submit_ichor_collate_log_job_to_auto_run(
    directory: Union[Path, MutableValue],
    hold: Optional[Union[JobID, List[JobID]]] = None,
) -> Optional[JobID]:
    if isinstance(directory, MutableValue):
        directory = directory.value

    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["collate_log"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job("collate_model_log", str(directory))
    with TimingManager(
        submission_script,
        message=f"Collating Model Log for {directory} child processes",
    ):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)


def submit_ichor_collate_models_to_auto_run(
    directory: Path,
    hold: Optional[Union[JobID, List[JobID]]] = None,
) -> JobID:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["collate_log"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job("collate_model_log", str(directory))
    with TimingManager(
        submission_script,
        message=f"Collating Models for {directory} child processes",
    ):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
