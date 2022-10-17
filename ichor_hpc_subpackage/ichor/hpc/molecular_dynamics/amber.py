from pathlib import Path
from ichor.hpc.batch_system import JobID
from ichor.core.useful_functions.get_atoms import get_atoms_from_path
from ichor.core.common.io import mkdir
from ichor.core.files import Mol2
from ichor.core.molecular_dynamics.amber import write_mdin
from ichor.hpc.submission_script import SubmissionScript, SCRIPT_NAMES, AmberCommand
from typing import Union
from ichor.hpc import  FILE_STRUCTURE

def submit_amber(
    input_file_path: Union[str, Path], temperature: int, nsteps: int = 1_000_000, write_coord_every: int = 10,
    system_name: str = None, ncores: int = 2, dt = 0.001, ln_gamma=0.7
) -> JobID:
    """
    Submits an amber job to compute node.

    :param input_file_path: A XYZ, GJF, PointsDirectory (uses 1st point), or PointDirectory Path
    :param temperature: The temperature to run the simulation at
    :param nsteps: The number of timesteps in the simulation, defaults to 1_000_000
    :param write_coord_every: Write out coordinates to mdcrd file every nth timestep, defaults to 10
    :param system_name: The name of the system. If left to None, then the name of the file `input_file_path` is used, defaults to None
    :param ncores: The number of cores to use for the job. Note that even though 2 cores are used, AMBER only runs in serial (1 core)
        for a single moleucle simulation. However, running on 2 cores means that the CSF3 1-core queue is omitted as it can be long.
        , defaults to 2
    :param dt: Timestep time in picoseconds, default is 0.001
    :param ln_gamma: The collision frequency in picoseconds, defaults to 0.7
    :return: A JobID instance containing information about the submitted job.
    """

    input_file_path = Path(input_file_path)
    atoms = get_atoms_from_path(input_file_path)
    # convert to Angstroms if not in Angstroms already, as Amber works with angstroms
    atoms = atoms.to_angstroms()

    if not system_name:
        system_name = input_file_path.stem

    # TODO: CSF3 1 job queue is slow, so run on 2 cores
    # number of residues is fixed at 1 as we aren't hydrating
    # nres = 1
    # # ncores must be less than or equal to the number of residues
    # ncores = min(ncores, nres)

    mkdir(FILE_STRUCTURE["amber"])
    mol2 = Mol2(FILE_STRUCTURE["amber"] / (system_name + Mol2.filetype), system_name, atoms)
    mol2.write()

    mdin = FILE_STRUCTURE["amber"] / "md.in"
    write_mdin(mdin, nsteps=nsteps, dt=dt, temperature=temperature,
               write_coordinates_every=write_coord_every, ln_gamma=ln_gamma,
    )

    with SubmissionScript(SCRIPT_NAMES["amber"], ncores=ncores) as submission_script:
        submission_script.add_command(AmberCommand(mol2_file=mol2.path, mdin_file=mdin, system_name=system_name,
                                                   temperature=temperature, ncores=ncores))
    return submission_script.submit()
