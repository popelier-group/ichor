from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)


def submit_gjfs(directory, hold: Optional[JobID] = None) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["gaussian"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("submit_gjfs", str(directory))
    submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
