from pathlib import Path
from typing import Optional, Union, List

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)

# matt_todo: better naming for file and function, new file so I have not documented yet
def submit_collate_log(
    directory: Path,
    hold: Optional[Union[JobID, List[JobID]]] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["aimall"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("collate_model_log", str(directory))
    with TimingManager(submission_script, message=f"Collating Model Log for {directory} child processes"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
