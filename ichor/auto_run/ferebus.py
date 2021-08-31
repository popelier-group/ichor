from pathlib import Path
from typing import List, Optional

from ichor.batch_system import JobID
from ichor.common.types import MutableValue
from ichor.submission_script import (SCRIPT_NAMES, FerebusCommand,
                                     SubmissionScript, TimingManager)

# todo: better naming for file and function
def auto_run_ferebus(
    ferebus_directory: Path, atoms: MutableValue, hold: Optional[JobID] = None
) -> Optional[JobID]:
    """ Submits a job to compute nodes that runs FEREBUS. FEREBUS can be ran on each atom separately (since each atom has its own model and its own
    adaptive sampling)."""
    script_name = SCRIPT_NAMES["ferebus"]
    ferebus_script = SubmissionScript(script_name)
    ferebus_directories = [ferebus_directory / atom for atom in atoms.value]
    with TimingManager(ferebus_script):
        for ferebus_atom_directory in ferebus_directories:
            ferebus_script.add_command(FerebusCommand(ferebus_atom_directory))
    ferebus_script.write()
    return ferebus_script.submit(hold=hold)
