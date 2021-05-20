from pathlib import Path
from typing import Optional, List

from ichor.batch_system import JobID
from ichor.submission_script import (SCRIPT_NAMES, FerebusCommand, ICHORCommand,
                                     SubmissionScript)


def auto_run_ferebus(
    ferebus_directory: Path, atoms: List[str], hold: Optional[JobID] = None
) -> Optional[JobID]:
    script_name = SCRIPT_NAMES["ferebus"]
    ferebus_script = SubmissionScript(script_name)
    ferebus_directories = [ferebus_directory / atom for atom in atoms]
    for ferebus_atom_directory in ferebus_directories:
        ferebus_script.add_command(FerebusCommand(ferebus_atom_directory))
    move_models = ICHORCommand()
    move_models.run_function("move_models")
    ferebus_script.add_command()
    ferebus_script.write()
    return ferebus_script.submit(hold=hold)
