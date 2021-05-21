from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def submit_wfns(
    directory: Path,
    atoms: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["aimall"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("submit_wfns", str(directory), atoms)
    with TimingManager(submission_script, message="Submitting WFNs"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
