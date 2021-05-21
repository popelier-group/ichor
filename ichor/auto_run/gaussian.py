from pathlib import Path
from typing import Optional, Union

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, TimingManager)
from ichor.common.types import MutableInt


def auto_run_gaussian(
    npoints: MutableInt, hold: Optional[JobID] = None
) -> Optional[JobID]:
    script_name = SCRIPT_NAMES["gaussian"]

    gauss_script = SubmissionScript(script_name)
    with TimingManager(gauss_script):
        for point in range(npoints.value):
            gauss_script.add_command(GaussianCommand(Path(f"Point{point+1}")))
    gauss_script.write()
    return gauss_script.submit(hold=hold)
