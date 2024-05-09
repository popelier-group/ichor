from pathlib import Path
from typing import Union

import ichor.hpc.global_variables

from ichor.core.common.io import mkdir
from ichor.core.files import GJF, XYZ
from ichor.core.molecular_dynamics.cp2k import write_cp2k_input
from ichor.hpc.batch_system.jobs import JobID

from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_commands import CP2KCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_cp2k(
    input_file: Union[str, Path],
    system_name: str,
    temperature: int,
    nsteps: int,
    method: str = "BLYP",
    basis_set: str = "6-31G*",
    molecular_charge: int = 0,
    spin_multiplicity: int = 1,
    ncores=2,
) -> JobID:
    """Submits a CP2K job to a compute node.

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
    :rtype: ichor.hpc.batch_system.jobs.JobID
    """

    input_file = Path(input_file)

    if XYZ.check_path(input_file):
        atoms = XYZ(input_file).atoms
    elif GJF.check_path(input_file):
        atoms = GJF(input_file).atoms
    else:
        raise ValueError(f"Unknown filetype: {input_file}")

    mkdir(ichor.hpc.global_variables.FILE_STRUCTURE["cp2k"])
    cp2k_input = (
        ichor.hpc.global_variables.FILE_STRUCTURE["cp2k"] / f"{system_name}.inp"
    )

    write_cp2k_input(
        cp2k_input,
        atoms,
        temperature,
        nsteps,
        Path(
            get_param_from_config(
                ichor.hpc.global_variables.ICHOR_CONFIG,
                ichor.hpc.global_variables.MACHINE,
                "software",
                "cp2k",
                "data_path",
            )
        ),
        system_name,
        method,
        basis_set,
        molecular_charge,
        spin_multiplicity,
    )

    with SubmissionScript(
        ichor.hpc.global_variables.SCRIPT_NAMES["cp2k"], ncores=ncores
    ) as submission_script:
        submission_script.add_command(
            CP2KCommand(cp2k_input, temperature, ncores, system_name)
        )
    return submission_script.submit()
