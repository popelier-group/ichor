from pathlib import Path
from typing import Optional

from ichor.batch_system import JobID
from ichor.globals import GLOBALS
from ichor.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                     SubmissionScript, TimingManager)


def adaptive_sampling(
    model_directory: Path = GLOBALS.FILE_STRUCTURE["models"],
    sample_pool_directory: Path = GLOBALS.FILE_STRUCTURE["sample_pool"],
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    submission_script = SubmissionScript(
        SCRIPT_NAMES["ichor"]["adaptive_sampling"]
    )
    ichor_command = ICHORCommand()
    ichor_command.run_function(
        "adaptive_sampling", str(model_directory), str(sample_pool_directory)
    )
    with TimingManager(submission_script, message="Adaptive Sampling"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
