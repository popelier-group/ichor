from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def make_models(
    directory: Path,
    atoms: Optional[List[str]] = None,
    ntrain: Optional[int] = None,
    types: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["ferebus"])
    ichor_command = ICHORCommand()
    ichor_command.run_function(
        "make_models",
        str(directory),
        str(atoms.value),
        str(ntrain),
        str(types),
    )
    with TimingManager(submission_script, message="Making Models"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
