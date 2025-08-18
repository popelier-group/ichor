from pathlib import Path
from typing import Union

import ichor.hpc.global_variables

from ichor.core.common.io import mkdir
from ichor.core.files import Mol2
from ichor.core.molecular_dynamics.amber import write_mdin
from ichor.core.useful_functions.get_atoms import get_atoms_from_path
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_commands import PythonCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_metadynamics(
    input_file_path: Union[str, Path],
    timestep: float = 0.005,
    bias: float = 5,
    nsteps: int = 1024,
    temperature: float = 298,
    system_name: str = None,
    ncores: int = 2,
    calculator: str = "GFN2-xTB",
) -> JobID:
    """
    Submits an amber job to compute node.

    :param input_file_path: A XYZ, GJF, PointsDirectory (uses 1st point), or PointDirectory Path
    :param temperature: The temperature to run the simulation at
    :param nsteps: The number of timesteps in the simulation, defaults to 1_000_000
    :param write_coord_every: Write out coordinates to mdcrd file every nth timestep, defaults to 10
    :param system_name: The name of the system. If left to None,
        then the name of the file `input_file_path` is used, defaults to None
    :param ncores: The number of cores to use for the job.
        Note that even though 2 cores are used, AMBER only runs in serial (1 core)
        for a single moleucle simulation. However, running on 2
        cores means that the CSF3 1-core queue is omitted as it can be long.
        , defaults to 2
    :param dt: Timestep time in picoseconds, default is 0.001
    :param ln_gamma: The collision frequency in picoseconds, defaults to 0.7
    :return: A JobID instance containing information about the submitted job.
    """

    print("PLACEHOLDER FOR METADYNAMICS SUBMISSION")
