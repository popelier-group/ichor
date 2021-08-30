from typing import Optional

from ichor.submission_script.ichor import ICHORCommand
from ichor.submission_script.submision_script import SubmissionScript

# matt_todo: I think timing_manager.py is a bit ambiguous name. Make into something like timing_manager_submission_script.py to be more precise.
# because all it does it adds extra lines to the submission script files, it doesn't run any timings itself
class TimingManager:
    """ A class that times how long jobs take. It uses the logging library, see `log_time` function.
    
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

        self.job_id = "$JOB_ID"
        self.task_id = "$SGE_TASK_ID"

    @property
    def identifier(self):
        return (
            f"{self.submission_script.path.name}:{self.job_id}:{self.task_id}"
        )

    def __enter__(self):
        python_job = ICHORCommand()
        if self.message:
            python_job.run_function(
                "log_time",
                f"START:{self.identifier}",
                self.message,
            )
        else:
            python_job.run_function("log_time", f"START:{self.identifier}")
        self.submission_script.add_command(python_job)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        python_job = ICHORCommand()
        python_job.run_function("log_time", f"FINISH:{self.identifier}")
        self.submission_script.add_command(python_job)
