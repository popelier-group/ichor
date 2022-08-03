from pathlib import Path
from ichor.hpc.batch_system import JobID
from ichor.core.analysis.get_atoms import get_atoms_from_path
from ichor.core.common.io import mkdir
from ichor.core.files import Mol2
from ichor.core.molecular_dynamics.amber import write_mdin
from ichor.hpc.submission_script import (
    SubmissionScript,
    SCRIPT_NAMES,
    AmberCommand,
)


def submit_amber(
    input_file: Path, temperature: float, nsteps: int, write_coord_every: int
) -> JobID:
    from ichor.hpc import GLOBALS, FILE_STRUCTURE

    atoms = get_atoms_from_path(input_file)

    nres = 1  # number of residues is fixed at 1 as we aren't hydrating
    GLOBALS.AMBER_NCORES = min(
        GLOBALS.AMBER_NCORES, nres
    )  # ncores must be less than or equal to the number of residues

    mkdir(FILE_STRUCTURE["amber"])
    mol2 = Mol2(
        FILE_STRUCTURE["amber"] / (GLOBALS.SYSTEM_NAME + Mol2.filetype)
    )
    mol2.atoms = atoms
    mol2.write(system_name=GLOBALS.SYSTEM_NAME)

    mdin = FILE_STRUCTURE["amber"] / "md.in"
    write_mdin(
        mdin,
        nsteps=nsteps,
        dt=GLOBALS.AMBER_TIMESTEP,
        temperature=temperature,
        write_coordinates_every=write_coord_every,
        ln_gamma=GLOBALS.AMBER_LN_GAMMA,
    )

    with SubmissionScript(SCRIPT_NAMES["amber"]) as submission_script:
        submission_script.add_command(
            AmberCommand(mol2.path, mdin, temperature)
        )
    return submission_script.submit()
