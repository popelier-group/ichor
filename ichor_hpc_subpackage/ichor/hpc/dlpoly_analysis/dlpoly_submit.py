from pathlib import Path
from typing import List, Optional

from ichor.core.calculators.geometry_calculator import get_internal_feature_indices
from ichor.core.useful_functions import get_atoms_from_path, get_models_from_path
from ichor.core.atoms import Atoms
from ichor.core.common.io import convert_to_path, ln, mkdir
from ichor.core.common.constants import dlpoly_weights
from ichor.core.models import Models
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.batch_system import JobID
from ichor.hpc.submission_script import SCRIPT_NAMES, DataLock, DlpolyCommand, ICHORCommand, SubmissionScript
from ichor.hpc.submission_script.common import submit_gjf_files
from ichor.core.files.dl_poly import DlPolyControl, DlPolyConfig, DlPolyField

def write_control(
    system_name: str,
    ensemble: str = "nvt",
    thermostat: str = "hoover",
    hoover_number: float = 0.04,
    temperature: int = 1,
    timestep: float = 0.001,
    n_steps: int = 500,
    file_name: str = "CONTROL",
):
    """ Writes CONTROL file that DL_FFLUX needs to function. It is a modified version of the DL_POLY CONTROL file.
    The defaults of the function are used to perform a geometry optimization, so the settings are different
    that the default settings.

    :param system_name: The name of the system
    :parm ensemble: The ensemble to use for the simulation, defaults to nvt
    :param thermostat: The thermostat to use for the simulation, defaults to hoover (Nose-Hoover thermostat)
    :param hoover_number: The relaxation constant of Nose-Hoover thermostat in ps, defaults to 0.04
    :param temperature: The temperature to run the simulation at, defaults to 0.0 (note that simulation is actually ran at 10K)
        because `zero` keyword is also added.
    :param timestep: The timestep time, defaults to 0.001 ps
    :param n_steps: The number of timesteps for the simulation, defaults to 500
    """
    
    control_file = DlPolyControl(path=file_name, system_name=system_name, ensemble=ensemble,
                                 thermostat=thermostat, thermostat_settings=[hoover_number], temperature=temperature,
                                 timestep=timestep, n_steps=n_steps)
    control_file.write()


def write_config(atoms: Atoms, cell_size: float, system_name: str, file_name: str = "CONFIG"):
    """Writes CONFIG file that DL_FFLUX needs to run.

    :param atoms: An Atoms instance that is the starting geometry of the DL_FFLUX MD simulation
    :param cell_size: The box size. Default is 50x50x50 Angstroms. Can be a cube only.
    :param system_name: The system name
    :parm file_name: The name of the config file. It has to be `CONFIG` to be read in correctly by DL_FFLUX.
    """
    
    # center atoms if the coordinates are very large, so that molecule is in box size.
    atoms.centre()
    dl_poly_config = DlPolyConfig(path=file_name, system_name=system_name, atoms=atoms, cell_size=cell_size)
    dl_poly_config.write()

def write_field(atoms: Atoms, system_name: str, file_name = "FIELD"):
    """Writes out DL FFLUX FIELD file.

    :param atoms: An Atoms instance which contains a geometry of the chemical system of interest.
    :param system_name: The name of the system
    :param file_name: The FIELD file name, defaults to "FIELD"
    """

    field_file = DlPolyField(path=file_name, atoms=atoms, system_name=system_name)
    field_file.write()

def link_models(path: Path, models: Models):
    model_dir = path / "model_krig"
    mkdir(model_dir)
    for model in models:
        ln(model.path.absolute(), model_dir)


def setup_dlpoly_directory(
    path: Path, atoms: Atoms, models: Models, temperature: float = 0.0
):
    mkdir(path)
    write_control(path, temperature=temperature)
    write_config(path, atoms)
    write_field(path, atoms)
    link_models(path, models)


def get_dlpoly_directories(models: List[Models]) -> List[Path]:
    dlpoly_directories = []
    for model in models:
        dlpoly_directories.append(
            FILE_STRUCTURE["dlpoly"]
            / f"{model.system}{str(model.ntrain).zfill(4)}"
        )
    return dlpoly_directories


@convert_to_path
def setup_dlpoly_directories(
    atoms: Atoms, models: List[Models], temperature: float = 0.0
) -> List[Path]:
    dlpoly_directories = get_dlpoly_directories(models)
    for dlpoly_dir, model in zip(dlpoly_directories, models):
        setup_dlpoly_directory(
            dlpoly_dir, atoms, model, temperature=temperature
        )
    return dlpoly_directories


def run_dlpoly(
    dlpoly_input: Path,
    model_location: Path,
    temperature: float = 0.0,
    hold=Optional[JobID],
) -> JobID:
    dlpoly_input_atoms = get_atoms_from_path(dlpoly_input)
    dlpoly_input_models = get_models_from_path(model_location)
    dlpoly_directories = setup_dlpoly_directories(
        dlpoly_input_atoms, dlpoly_input_models, temperature=temperature
    )
    return submit_dlpoly_jobs(dlpoly_directories, hold=hold)


def run_dlpoly_geometry_optimisations(
    dlpoly_input: Path, model_location: Path, hold=Optional[JobID]
) -> JobID:
    return run_dlpoly(dlpoly_input, model_location, temperature=0.0)


def write_final_geometry_to_gjf(
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
) -> List[Path]:

    from ichor.core.files import GJF, DlpolyHistory

    gjfs = []
    for d in dlpoly_directory.iterdir():
        if d.is_dir() and (d / "HISTORY").exists():
            dlpoly_history = DlpolyHistory(d / "HISTORY")
            gjf = GJF(d / (d.name + GJF.filetype))
            gjf.atoms = dlpoly_history[-1]
            gjf._write_file()
            gjfs += [gjf.path]
    return gjfs


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


def submit_dlpoly_jobs(
    dlpoly_directories: List[Path], hold: Optional[JobID] = None
) -> JobID:
    with SubmissionScript(SCRIPT_NAMES["dlpoly"]) as submission_script:
        for dlpoly_directory in dlpoly_directories:
            submission_script.add_command(DlpolyCommand(dlpoly_directory))
    return submission_script.submit(hold=hold)


def submit_write_dlpoly_gjfs(
    dlpoly_directory: Path, hold: Optional[JobID] = None
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["ichor"]["dlpoly"]["gaussian"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="submit_final_geometry_to_gaussian",
                func_args=[str(dlpoly_directory)],
            )
        )
    return submission_script.submit(hold=hold)


def submit_dlpoly_gjfs(
    gjfs: List[Path], hold: Optional[JobID] = None
) -> JobID:
    return submit_gjf_files(gjfs, hold=hold)


def submit_dlpoly_energies(
    dlpoly_directory: Path, hold: Optional[JobID] = None
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["ichor"]["dlpoly"]["energies"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="get_dlpoly_energies",
                func_args=[str(dlpoly_directory)],
            )
        )
    return submission_script.submit(hold=hold)


def submit_dlpoly_optimisation_analysis_auto_run(
    dlpoly_input: Path,
    model_location: Path,
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
    hold: Optional[JobID] = None,
) -> JobID:
    ninputs = len(get_models_from_path(model_location))
    dummy_paths = [Path("tmp.file") for _ in range(ninputs)]
    with DataLock():
        job_id = submit_setup_dlpoly_directories(
            dlpoly_input, model_location, hold=hold
        )
        job_id = submit_dlpoly_jobs(dummy_paths, hold=job_id)
        job_id = submit_write_dlpoly_gjfs(dlpoly_directory, hold=job_id)
        job_id = submit_dlpoly_gjfs(dummy_paths, hold=job_id)
        job_id = submit_dlpoly_energies(dlpoly_directory, hold=job_id)
    return job_id
