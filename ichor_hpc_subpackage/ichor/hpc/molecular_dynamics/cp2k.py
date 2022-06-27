from pathlib import Path

from ichor.core.common.io import mkdir
from ichor.core.files import GJF, XYZ
from ichor.core.molecular_dynamics.cp2k import write_cp2k_input
from ichor.hpc.batch_system import JobID
from ichor.hpc.machine import Machine
from ichor.hpc.submission_script import (
    SCRIPT_NAMES,
    CP2KCommand,
    SubmissionScript,
)

datafile_location = {
    Machine.ffluxlab: Path("/home/modules/apps/cp2k/6.1.0/data"),
    Machine.csf3: Path("/opt/apps/apps/intel-17.0/cp2k/6.1.0/data"),
    Machine.local: Path("$CP2K_HOME/data"),
}


def submit_cp2k(input_file: Path, temperature: float, nsteps: int) -> JobID:
    from ichor.hpc import FILE_STRUCTURE, GLOBALS, MACHINE

    if input_file.suffix == XYZ.filetype:
        atoms = XYZ(input_file).atoms
    elif input_file.suffix == GJF.filetype:
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    mkdir(FILE_STRUCTURE["cp2k"])
    cp2k_input = FILE_STRUCTURE["cp2k"] / f"{GLOBALS.SYSTEM_NAME}.inp"
    write_cp2k_input(
        cp2k_input,
        atoms,
        temperature,
        nsteps,
        datafile_location[MACHINE],
        GLOBALS.SYSTEM_NAME,
        GLOBALS.CP2K_METHOD,
        GLOBALS.CP2K_BASIS_SET,
    )

    with SubmissionScript(SCRIPT_NAMES["cp2k"]) as submission_script:
        submission_script.add_command(CP2KCommand(cp2k_input, temperature))
    return submission_script.submit()
