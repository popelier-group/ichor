from typing import Optional

from ichor.hpc.submission_script.ichor_command import ICHORCommand
from ichor.hpc.submission_script.submission_script import SubmissionScript


class TimingManager:
    """A class that times how long jobs take. It uses the logging library, see `log_time` function.

    :param submission_script: A SubmissionScript instance (which represents a job) that is going to be timed.
    :param message: A string to write in the logger.
    """

    def __init__(
        self,
        submission_script: SubmissionScript,
        message: Optional[str] = None,
    ):
        self.submission_script = submission_script
        self.message = message

    @property
    def job_id(self) -> str:
        from ichor.hpc import BATCH_SYSTEM

        return f"${BATCH_SYSTEM.JobID}"

    @property
    def task_id(self) -> str:
        from ichor.hpc import BATCH_SYSTEM

        return f"${BATCH_SYSTEM.TaskID}"

    @property
    def identifier(self):
        return f"{self.submission_script.path.name}:{self.job_id}:{self.task_id}"

    def __enter__(self):
        python_job = ICHORCommand()
        if self.message:
            python_job.add_function_to_job(
                "log_time",
                f"START:{self.identifier}",
                self.message,
            )
        else:
            python_job.add_function_to_job("log_time", f"START:{self.identifier}")
        self.submission_script.add_command(python_job)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        python_job = ICHORCommand()
        python_job.add_function_to_job("log_time", f"FINISH:{self.identifier}")
        self.submission_script.add_command(python_job)
