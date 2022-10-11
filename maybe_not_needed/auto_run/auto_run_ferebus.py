from pathlib import Path
from typing import List, Optional, Union

from ichor.core.common.types import MutableValue
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import (SCRIPT_NAMES, FerebusCommand,
                                         SubmissionScript, TimingManager)


def submit_ferebus_job_to_auto_run(
    ferebus_directory: Union[MutableValue, Path],
    atoms: MutableValue,
    hold: Optional[JobID] = None,
) -> Optional[JobID]:
    """Submits a job to compute nodes that runs FEREBUS. FEREBUS can be ran on each atom separately (since each atom has its own model and its own
    adaptive sampling)."""
    if isinstance(ferebus_directory, MutableValue):
        ferebus_directory = ferebus_directory.value
    script_name = SCRIPT_NAMES["ferebus"]
    ferebus_script = SubmissionScript(script_name)
    ferebus_directories = [ferebus_directory / atom for atom in atoms.value]
    with TimingManager(ferebus_script):
        for ferebus_atom_directory in ferebus_directories:
            ferebus_script.add_command(FerebusCommand(ferebus_atom_directory))
    ferebus_script.write()
    return ferebus_script.submit(hold=hold)
