from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript)


def submit_wfns(
    directory: Path, hold: Optional[JobID] = None
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["aimall"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("submit_wfns", str(directory))
    submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
