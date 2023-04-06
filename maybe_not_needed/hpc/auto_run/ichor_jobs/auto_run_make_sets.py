from pathlib import Path
from typing import Optional, Union

from ichor.core.common.types import MutableValue
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                         SubmissionScript, TimingManager)


def submit_make_sets_job_to_auto_run(
    points_input: Union[Path, MutableValue], hold: Optional[JobID] = None
) -> Optional[JobID]:
    """Submits a job to the workload manager which creates the initial traning/sample pool/validation set directories.

    :return: Returns the job ID which was assigned by the workload manager
    """
    if isinstance(points_input, MutableValue):
        points_input = points_input.value

    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["make_sets"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job("make_sets", str(points_input))
    with TimingManager(submission_script, message="Make Sets"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
