from pathlib import Path
from typing import List, Optional, Union

from ichor.core.common.types import MutableValue
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, ICHORCommand,
                                         SubmissionScript, TimingManager)


def make_models(
    directory: Union[Path, MutableValue],
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    ntrain: Optional[int] = None,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Write out datafiles and settings needed by FEREBUS. The actual FEREBUS calculations are done in the next job. Returns the job ID of this job,
    which is assigned by the workload manager (SGE,SLURM, etc.)."""
    if isinstance(directory, MutableValue):
        directory = directory.value

    submission_script = SubmissionScript(SCRIPT_NAMES["ichor"]["ferebus"])
    ichor_command = ICHORCommand(auto_run=True)
    ichor_command.add_function_to_job(
        "make_models",
        str(directory),
        str(atoms.value),
        str(ntrain),
        str(types.value),
    )
    # todo: This function submits jobs which write out datafile, it does not make models.
    with TimingManager(submission_script, message="Making Models"):
        submission_script.add_command(ichor_command)
    submission_script.write()
    return submission_script.submit(hold=hold)
