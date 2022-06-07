from pathlib import Path
from typing import Optional, Union

from ichor.hpc.batch_system import JobID
from ichor.core.common.types import MutableValue
from ichor.hpc.submission_script import (SCRIPT_NAMES, GaussianCommand,
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
            # todo: Why is this f"Point{point+1}" needed, it doesn't point to any real file, it is just to make the same number of GaussianCommands as number of points
            gauss_script.add_command(
                GaussianCommand(Path(f"Point{point+1}"))
            )  # don't actually need the names of  the files here, we just need
            # to make the submission script contain the same number of GaussianCommands as the number of points
    gauss_script.write()
    return gauss_script.submit(hold=hold)
