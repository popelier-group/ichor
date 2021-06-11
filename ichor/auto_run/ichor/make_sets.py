from typing import Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)
from pathlib import Path


def make_sets(points_input: Path, hold: Optional[JobID] = None) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["make_sets"])
    ichor_command = ICHORCommand()
    ichor_command.run_function("make_sets", str(points_input))
    with TimingManager(submission_script, message="Make Sets"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
