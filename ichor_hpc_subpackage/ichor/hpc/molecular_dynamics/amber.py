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
    input_file_path: Union[str, Path], temperature: float, nsteps: int = 1_000_000, write_coord_every: int = 10,
    system_name: str = None, ncores: int = 1, dt = 0.001, ln_gamma=0.7
) -> JobID:

    input_file_path = Path(input_file_path)
    atoms = get_atoms_from_path(input_file_path)
    # convert to Angstroms if not in Angstroms already, as Amber works with angstroms
    atoms = atoms.to_angstroms()
    
    if not system_name:
        system_name = input_file_path.stem

    # number of residues is fixed at 1 as we aren't hydrating
    nres = 1
    # ncores must be less than or equal to the number of residues
    ncores = min(ncores, nres)

    mkdir(FILE_STRUCTURE["amber"])
    mol2 = Mol2(FILE_STRUCTURE["amber"] / (system_name + Mol2.filetype))
    mol2.atoms = atoms
    mol2.write()

    mdin = FILE_STRUCTURE["amber"] / "md.in"
    write_mdin(mdin, nsteps=nsteps, dt=dt, temperature=temperature,
               write_coordinates_every=write_coord_every, ln_gamma=ln_gamma,
    )

    with SubmissionScript(SCRIPT_NAMES["amber"], ncores=ncores) as submission_script:
        submission_script.add_command(AmberCommand(mol2.path, mdin, temperature))
    return submission_script.submit()
