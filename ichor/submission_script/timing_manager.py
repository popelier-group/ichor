from ichor.submission_script.ichor import ICHORCommand
from ichor.submission_script.submision_script import SubmissionScript
from typing import Optional


class TimingManager:
    def __init__(self, submission_script: SubmissionScript, message: Optional[str] = None):
        self.submission_script = submission_script
        self.message = message

        self.job_id = "$JOB_ID"
        self.task_id = "$SGE_TASK_ID"

    @property
    def identifier(self):
        return f"{self.submission_script.path}:{self.job_id}:{self.task_id}"

    def __enter__(self):
        python_job = ICHORCommand()
        if self.message:
            python_job.run_function(
                "log_time", f"START:{self.identifier}", self.message,
            )
        else:
            python_job.run_function("log_time", f"START:{self.identifier}")
        self.submission_script.add_command(python_job)

    def __exit__(self, exc_type, exc_value, exc_traceback):
        python_job = ICHORCommand()
        python_job.run_function("log_time", f"FINISH:{self.identifier}")
        self.submission_script.add_command(python_job)