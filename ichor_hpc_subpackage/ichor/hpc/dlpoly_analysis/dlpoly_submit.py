from pathlib import Path
from typing import List, Optional

from ichor.core.useful_functions import get_atoms_from_path, get_models_from_path
from ichor.core.atoms import Atoms
from ichor.core.common.io import mkdir, copyfile, pushd, ln
from ichor.core.models import Model
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import SCRIPT_NAMES, DataLock, DlpolyCommand, ICHORCommand, SubmissionScript
from ichor.hpc.submission_script.common import submit_gjf_files
from ichor.core.useful_functions.dl_poly.dl_poly_write_optimization_files import write_config, write_control, write_field
from ichor.core.useful_functions.dl_poly.write_final_geometry_to_gjf import write_final_geometry_to_gjf

def symlink_models(dl_poly_directory_path: Path, models_directory: Path):
    """Creates symbolic link to models in `models_directory` inside
    a directory called `model_krig` in `dl_poly_directory_path`.

    :param dl_poly_directory_path: _description_
    :type dl_poly_directory_path: Path
    :param models_directory: _description_
    :type models_directory: Path
    """

    model_dir = dl_poly_directory_path / "model_krig"
    mkdir(model_dir)
    for model in models_directory.iterdir():
        if model.suffix == Model.filetype:
            ln(model.absolute(), model_dir)

def copy_models(dl_poly_directory_path: Path, models_directory: Path):
    """Copies all model files to the `model_krig` directory, which is in the directory where DL POLY will be ran.

    :param dl_poly_directory_path: The directory path where DL POLY will be ran
    :param models_directory: A Path object to directory containing .model files that DL POLY uses to make predictions
    """
    
    model_dir = dl_poly_directory_path / "model_krig"
    mkdir(model_dir)
    for model in models_directory.iterdir():
        if model.suffix == Model.filetype:
            copyfile(model.absolute(), model_dir)

def setup_dlpoly_directory(dl_poly_job_directory_path: Path, system_name:str,
                           atoms: Atoms, models_directory: Path, temperature: int = 1):
    """Sets up a DL POLY directory where the DL POLY job will be ran

    :param dl_poly_directory_path: Path to DL POLY directory
    :param atoms: Instance of Atoms which contains the initial geometry for DL POLY
    :param models_directory: A Path object to directory containing .model files that DL POLY uses to make predictions
    :param temperature: The temperature at which to run the simulation, defaults to 1
    """
    
    # make the parent directory where the DL POLY job will be ran
    mkdir(dl_poly_job_directory_path)
    # change into the new directory and write out the CONTROL, CONFIG, FIELD files
    with pushd(dl_poly_job_directory_path):
        write_control(system_name, temperature=temperature)
        write_config(atoms=atoms, system_name=system_name)
        write_field(atoms=atoms, system_name=system_name)
    # copy over model files to model_krig inside the job directory
    copy_models(dl_poly_job_directory_path, models_directory)

def submit_dlpoly_job(
    file_containing_atoms: Path,
    models_directory: Path,
    system_name: str,
    dl_poly_executable_path: Path,
    ncores: int = 1, 
    temperature: int = 1,
    cell_size: float = 50.0,
    dl_poly_job_directory: Path = Path("DL_FFLUX_RUN"),
    hold: Optional[JobID] = None,
) -> JobID:
    
    atoms_instance = get_atoms_from_path(file_containing_atoms)
    setup_dlpoly_directory(dl_poly_job_directory, system_name, atoms_instance, models_directory, temperature=temperature,
                           cell_size=cell_size)
    
    with SubmissionScript(SCRIPT_NAMES["dlpoly"], ncores=ncores) as submission_script:
        submission_script.add_command(DlpolyCommand(dl_poly_executable_path, dl_poly_job_directory))
    return submission_script.submit(hold=hold)

def submit_final_geometry_from_history_to_gaussian(
    dlpoly_directory: Path,
    hold: Optional[JobID] = None,
    **kwargs
) -> JobID:
    """
    Runs the last geometry that was found in the DL POLY HISTORY file to Gaussian.

    :param dlpoly_directory: The directory containing the DL POLY run with HISTORY file.
    :param hold: A JobID to hold this job for, defaults to None
    :param kwargs: Key word arguments to pass to GJF class. These can be things like basis set or level of theory.
    :return: Returns the JobID of the submitted job.
    """
    gjfs = write_final_geometry_to_gjf(dlpoly_directory, **kwargs)
    return submit_gjf_files(gjfs, hold=hold)


# # TODO: fix these after fixing the ichor command to activate the conda environment with ichor installed.

# def submit_setup_dlpoly_directory(dl_poly_job_directory_path: Path, system_name:str,
#                            file_containing_atoms: Path, models_directory: Path, temperature: int = 1
#                            ) -> JobID:
#     """Submitted to compute node. Sets up a DL POLY directory where the DL POLY job will be ran.

#     :param dl_poly_directory_path: Path to DL POLY directory
#     :param atoms: Instance of Atoms which contains the initial geometry for DL POLY
#     :param models_directory: A Path object to directory containing .model files that DL POLY uses to make predictions
#     :param temperature: The temperature at which to run the simulation, defaults to 1
#     """
    
#     atoms_instance = get_atoms_from_path(file_containing_atoms)
    
#     with SubmissionScript(
#         SCRIPT_NAMES["ichor"]["dlpoly"]["setup"]
#     ) as submission_script:
#         submission_script.add_command(
#             ICHORCommand(
#                 func="setup_dlpoly_directory",
#                 func_args=[str(dl_poly_job_directory_path), str(system_name), ],
#             )
#         )
#     return submission_script.submit(hold=hold)


# def submit_dlpoly_optimisation_analysis_auto_run(
#     file_containing_atoms: Path,
#     models_directory: Path,
#     dlpoly_job_directory: Path = FILE_STRUCTURE["dlpoly"],
#     hold: Optional[JobID] = None,
# ) -> JobID:
    
#     ninputs = len(get_models_from_path(model_location))
    
#     job_id = submit_setup_dlpoly_directories(
#         dlpoly_input, model_location, hold=hold
#     )
#     job_id = submit_dlpoly_jobs(dummy_paths, hold=job_id)
#     job_id = submit_write_dlpoly_gjfs(dlpoly_directory, hold=job_id)
#     job_id = submit_dlpoly_gjfs(dummy_paths, hold=job_id)
#     job_id = submit_dlpoly_energies(dlpoly_directory, hold=job_id)
#     return job_id





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