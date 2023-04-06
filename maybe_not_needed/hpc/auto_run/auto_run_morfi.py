from pathlib import Path
from typing import List, Optional

from ichor.core.common.types import MutableValue
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, MorfiCommand,
                                         SubmissionScript, TimingManager)


def submit_morfi_job_to_auto_run(
    npoints: MutableValue,
    atoms: MutableValue = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Submit an AIMALL job to the workload manager. This job generates .int files."""
    script_name = SCRIPT_NAMES["pandora"]["morfi"]
    morfi_script = SubmissionScript(script_name)
    with TimingManager(morfi_script):
        for point in range(npoints.value):
            morfi_script.add_command(
                MorfiCommand(
                    Path(f"Point{point+1}"),
                    Path(f"Point{point+1}"),
                    Path(f"Point{point+1}"),
                    atoms.value,
                )
            )
    morfi_script.write()
    return morfi_script.submit(hold=hold)
