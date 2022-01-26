from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.submission_script import (
    SCRIPT_NAMES,
    AIMAllCommand,
    GaussianCommand,
    SubmissionScript,
)


def submit_gjf_files(
    gjfs: List[Path],
    script_name: Path = SCRIPT_NAMES["gaussian"],
    hold: Optional[JobID] = None,
) -> JobID:
    with SubmissionScript(script_name) as submission_script:
        for gjf in gjfs:
            submission_script.add_command(GaussianCommand(gjf))
    return submission_script.submit(hold=hold)


def submit_wfn_files(
    wfns: List[Path],
    script_name: Path = SCRIPT_NAMES["aimall"],
    hold: Optional[JobID] = None,
) -> JobID:
    with SubmissionScript(script_name) as submission_script:
        for wfn in wfns:
            submission_script.add_command(AIMAllCommand(wfn))
    return submission_script.submit(hold=hold)
