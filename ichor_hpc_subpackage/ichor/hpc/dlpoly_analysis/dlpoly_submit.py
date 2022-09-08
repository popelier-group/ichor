from pathlib import Path
from typing import List, Optional

from ichor.core.useful_functions import get_atoms_from_path, get_models_from_path
from ichor.core.atoms import Atoms
from ichor.core.common.io import ln, mkdir
from ichor.core.models import Models
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import SCRIPT_NAMES, DataLock, DlpolyCommand, ICHORCommand, SubmissionScript
from ichor.hpc.submission_script.common import submit_gjf_files
from ichor.core.useful_functions.dl_poly.dl_poly_write_optimization_files import write_config, write_control, write_field
from ichor.core.useful_functions.dl_poly.write_final_geometry_to_gjf import write_final_geometry_to_gjf

def link_models(dl_poly_directory_path: Path, models: Models):
    """Creates a symbolic link to model files

    :param dl_poly_directory_path: The directory path where DL POLY will be ran
    :param models: An instance of Models (a class that wraps a directory containing model files)
    """
    
    model_dir = dl_poly_directory_path / "model_krig"
    mkdir(model_dir)
    for model in models:
        ln(model.path.absolute(), model_dir)


def setup_dlpoly_directory(dl_poly_directory_path: Path, atoms: Atoms, models: Models, temperature: int = 1):
    """Sets up a DL POLY directory where the DL POLY job will be ran

    :param dl_poly_directory_path: Path to DL POLY directory
    :param atoms: Instance of Atoms which contains the initial geometry for DL POLY
    :type models: An instance of Models (a class that wraps a directory containing model files)
    :param temperature: The temperature at which to run the simulation, defaults to 1
    """
    
    mkdir(dl_poly_directory_path)
    write_control(dl_poly_directory_path, temperature=temperature)
    write_config(dl_poly_directory_path, atoms)
    write_field(dl_poly_directory_path, atoms)
    link_models(dl_poly_directory_path, models)

def submit_dlpoly(
    file_containing_atoms: Path,
    models_directory: Path,
    temperature: int = 1,
    hold=Optional[JobID],
) -> JobID:
    
    dlpoly_input_atoms = get_atoms_from_path(file_containing_atoms)
    dlpoly_input_models = get_models_from_path(models_directory)
    dlpoly_directories = setup_dlpoly_directory(
        dlpoly_input_atoms, dlpoly_input_models, temperature=temperature
    )
    
    return submit_dlpoly_jobs(dlpoly_directories, hold=hold)

def run_dlpoly_geometry_optimisation(
    dlpoly_input: Path, model_location: Path, hold=Optional[JobID]
) -> JobID:
    return run_dlpoly(dlpoly_input, model_location, temperature=0.0)

def submit_final_geometry_to_gaussian(
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
    hold: Optional[JobID] = None,
) -> JobID:
    gjfs = write_final_geometry_to_gjf(dlpoly_directory)
    return submit_dlpoly_gjfs(gjfs, hold=hold)

def submit_setup_dlpoly_directories(
    dlpoly_input: Path,
    model_location: Path,
    hold: Optional[JobID] = None,
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["ichor"]["dlpoly"]["setup"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="run_dlpoly_geometry_optimisations",
                func_args=[str(dlpoly_input), str(model_location)],
            )
        )
    return submission_script.submit(hold=hold)

# TODO: fix these after fixing the ichor command to activate the conda environment with ichor installed.

# def submit_write_dlpoly_gjfs(
#     dlpoly_directory: Path, hold: Optional[JobID] = None
# ) -> JobID:
#     with SubmissionScript(
#         SCRIPT_NAMES["ichor"]["dlpoly"]["gaussian"]
#     ) as submission_script:
#         submission_script.add_command(
#             ICHORCommand(
#                 func="submit_final_geometry_to_gaussian",
#                 func_args=[str(dlpoly_directory)],
#             )
#         )
#     return submission_script.submit(hold=hold)

# def submit_dlpoly_optimisation_analysis_auto_run(
#     dlpoly_input: Path,
#     model_location: Path,
#     dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
#     hold: Optional[JobID] = None,
# ) -> JobID:
#     ninputs = len(get_models_from_path(model_location))
#     dummy_paths = [Path("tmp.file") for _ in range(ninputs)]
    
#     with DataLock():
#         job_id = submit_setup_dlpoly_directories(
#             dlpoly_input, model_location, hold=hold
#         )
#         job_id = submit_dlpoly_jobs(dummy_paths, hold=job_id)
#         job_id = submit_write_dlpoly_gjfs(dlpoly_directory, hold=job_id)
#         job_id = submit_dlpoly_gjfs(dummy_paths, hold=job_id)
#         job_id = submit_dlpoly_energies(dlpoly_directory, hold=job_id)
#     return job_id

# def submit_get_dlpoly_energies(
#     dlpoly_directory: Path, hold: Optional[JobID] = None
# ) -> JobID:
#     with SubmissionScript(
#         SCRIPT_NAMES["ichor"]["dlpoly"]["energies"]
#     ) as submission_script:
#         submission_script.add_command(
#             ICHORCommand(
#                 func="get_dlpoly_energies",
#                 func_args=[str(dlpoly_directory)],
#             )
#         )
#     return submission_script.submit(hold=hold)





# def submit_dlpoly_jobs(
#     dlpoly_directories: List[Path], hold: Optional[JobID] = None
# ) -> JobID:
#     with SubmissionScript(SCRIPT_NAMES["dlpoly"]) as submission_script:
#         for dlpoly_directory in dlpoly_directories:
#             submission_script.add_command(DlpolyCommand(dlpoly_directory))
#     return submission_script.submit(hold=hold)





# def run_dlpoly(
#     dlpoly_input: Path,
#     model_location: Path,
#     temperature: int = 1,
#     hold=Optional[JobID],
# ) -> JobID:
#     dlpoly_input_atoms = get_atoms_from_path(dlpoly_input)
#     dlpoly_input_models = get_models_from_path(model_location)
#     dlpoly_directories = setup_dlpoly_directories(
#         dlpoly_input_atoms, dlpoly_input_models, temperature=temperature
#     )
#     return submit_dlpoly_jobs(dlpoly_directories, hold=hold)


# def get_paths_to_dlpoly_directories(models: List[Models]) -> List[Path]:
#     """Returns a list of Paths to DL POLY directories. Each DL POLY directory has the
#     number of training points used in the model

#     :param models: _description_
#     :type models: List[Models]
#     :return: _description_
#     :rtype: List[Path]
#     """
    
#     dlpoly_directories = []
#     for model in models:
#         dlpoly_directories.append(
#             FILE_STRUCTURE["dlpoly"]
#             / f"{model.system}{str(model.ntrain).zfill(4)}"
#         )
#     return dlpoly_directories

# def setup_dlpoly_directories(
#     atoms: Atoms, models: List[Models], temperature: float = 0.0
# ) -> List[Path]:
#     dlpoly_directories = get_paths_to_dlpoly_directories(models)
#     for dlpoly_dir, model in zip(dlpoly_directories, models):
#         setup_dlpoly_directory(
#             dlpoly_dir, atoms, model, temperature=temperature
#         )
#     return dlpoly_directories