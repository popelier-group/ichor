from pathlib import Path
from typing import List, Optional, Union

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def submit_ichor_collate_log_job_to_auto_run(
    directory: Path,
    hold: Optional[Union[JobID, List[JobID]]] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["aimall"])
    ichor_command = ICHORCommand()
    ichor_command.add_function_to_job("collate_model_log", str(directory))
    with TimingManager(
        submission_script,
        message=f"Collating Model Log for {directory} child processes",
    ):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
