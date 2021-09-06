from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.file_structure import FILE_STRUCTURE
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def submit_ichor_active_learning_job_to_auto_run(
    model_directory: Path = FILE_STRUCTURE["models"],
    sample_pool_directory: Path = FILE_STRUCTURE["sample_pool"],
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Submits the adaptive sampling job that ICHOR performs. After FEREBUS job (previous job in the auto run sequence) is done, ICHOR performs
    the adaptive sampling step, which adds additional traning set points. Variance or prediction error are calculated for each point. The worst
    predicted point is added to the training set. After this step, the next iteration of auto run can begin.

    :return JobID: The job ID number assigned to this job after it was submitted to the workload manager (SLURM, SGE, etc.)
    """
    submission_script = SubmissionScript(
        SCRIPT_NAMES["ichor"]["active_learning"]
    )
    ichor_command = ICHORCommand()
    ichor_command.add_function_to_job(
        "active_learning", str(model_directory), str(sample_pool_directory)
    )
    with TimingManager(submission_script, message="Adaptive Sampling"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
