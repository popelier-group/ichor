from ichor.common.types.mutable_value import MutableValue
from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)
from ichor.common.types import MutableValue


def submit_wfns(
    directory: Path,
    atoms: Optional[MutableValue],
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["aimall"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("submit_wfns", str(directory), atoms.value)
    with TimingManager(submission_script, message="Submitting WFNs"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
