from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def submit_make_sets_job_to_auto_run(
    points_input: Path, hold: Optional[JobID] = None
) -> Optional[JobID]:
    """Submits a job to the workload manager which creates the initial traning/sample pool/validation set directories.

    :return: Returns the job ID which was assigned by the workload manager
    """
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["make_sets"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job("make_sets", str(points_input))
    with TimingManager(submission_script, message="Make Sets"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
