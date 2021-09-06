from pathlib import Path
from typing import Optional, Union

from ichor.batch_system import JobID
from ichor.common.types import MutableValue
from ichor.submission_script import (SCRIPT_NAMES, GaussianCommand,
                                     SubmissionScript, TimingManager)


def submit_gaussian_job_to_auto_run(
    npoints: MutableValue, hold: Optional[JobID] = None
) -> Optional[JobID]:
    """Writes out the Gaussian script that is needed to run all the individual Gaussian jobs that were written in the datafile in the previous
    job. This function submits the Gaussian script to compute nodes and returns the job ID that is assigned by the workload manager."""
    script_name = SCRIPT_NAMES["gaussian"]

    gauss_script = SubmissionScript(script_name)
    with TimingManager(gauss_script):
        for point in range(npoints.value):
            gauss_script.add_command(GaussianCommand(Path(f"Point{point+1}")))
    gauss_script.write()
    return gauss_script.submit(hold=hold)
