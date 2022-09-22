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
from ichor.hpc import FILE_STRUCTURE, MACHINE

datafile_location = {
    Machine.ffluxlab: Path("/home/modules/apps/cp2k/6.1.0/data"),
    Machine.csf3: Path("/opt/apps/apps/intel-17.0/cp2k/6.1.0/data"),
    Machine.local: Path("$CP2K_HOME/data"),
}


def submit_cp2k(input_file: Path, system_name: str, temperature: int, nsteps: int,
                    method: str = "BLYP", basis_set: str = "6-31G*", 
                    molecular_charge: int = 0, spin_multiplicity: int = 1,
                    ncores=2) -> JobID:
    """_summary_

    :param input_file: A XYZ (.xyz) or GJF (.gjf) file that contains the starting geometry.
    :param system_name:  The name of the chemical system
    :param temperature: The temperature at which to run the simulation
    :param nsteps: The number of timeteps to run the simulation for
    :param method: The method which to use for the simulation, defaults to "BLYP"
    :param basis_set: The basis set which to use for the simulation, defaults to "6-31G*"
    :param molecular_charge: The charge of the system, defaults to 0
    :param spin_multiplicity: The spin multiplicity of the system, defaults to 1
    :param ncores: The number of cores to use for the simulation, defaults to 2
    :raises ValueError: If incorrect filetype (not xyz or gjf) is passed in
    :return: An object containing information for the submitted job
    :rtype: JobID
    """

    if input_file.suffix == XYZ.filetype:
        atoms = XYZ(input_file).atoms
    elif input_file.suffix == GJF.filetype:
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    mkdir(FILE_STRUCTURE["cp2k"])
    cp2k_input = FILE_STRUCTURE["cp2k"] / f"{system_name}.inp"

    write_cp2k_input(
        cp2k_input,
        atoms,
        temperature,
        nsteps,
        datafile_location[MACHINE],
        system_name,
        method,
        basis_set,
        molecular_charge,
        spin_multiplicity
    )

    with SubmissionScript(SCRIPT_NAMES["cp2k"], ncores=ncores) as submission_script:
        submission_script.add_command(CP2KCommand(cp2k_input, temperature, ncores, system_name))
    return submission_script.submit()
