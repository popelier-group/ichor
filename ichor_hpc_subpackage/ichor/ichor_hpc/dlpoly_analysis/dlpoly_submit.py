from pathlib import Path
from typing import List, Optional

from ichor.ichor_lib.analysis.get_models import get_models_from_path
from ichor.ichor_hpc.batch_system import JobID
from ichor.ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_hpc.submission_script import (SCRIPT_NAMES, DataLock, DlpolyCommand,
                                     ICHORCommand, SubmissionScript)
from ichor.ichor_hpc.submission_script.common import submit_gjf_files

def write_control(path: Path, temperature: float = 0.0):
    with open(path / "CONTROL", "w+") as f:
        f.write(f"Title: {GLOBALS.SYSTEM_NAME}\n")
        f.write("\n")
        f.write(f"ensemble nvt hoover {GLOBALS.DLPOLY_HOOVER}\n")
        f.write("\n")
        if int(temperature) == 0:
            f.write("temperature 0\n")
            f.write("\n")
            f.write("#perform zero temperature run (really set to 10K)\n")
            f.write("zero\n")
            f.write("\n")
        else:
            f.write(f"temperature {temperature}\n")
            f.write("\n")
        f.write("\n")
        f.write(f"timestep {GLOBALS.DLPOLY_TIMESTEP}\n")
        f.write(f"steps {GLOBALS.DLPOLY_NUMBER_OF_STEPS}\n")
        f.write("scale 100\n")
        f.write("\n")
        f.write("cutoff  8.0\n")
        f.write("rvdw    8.0\n")
        f.write("vdw direct\n")
        f.write("vdw shift\n")
        f.write("fflux cluster L1\n")
        f.write("\n")
        f.write("dump  1000\n")
        f.write("traj 0 1 0\n")
        f.write("print every 1\n")
        f.write("stats every 1\n")
        f.write("fflux print 0 1\n")
        f.write("job time 10000000\n")
        f.write("close time 20000\n")
        f.write("finish\n")


def write_config(path: Path, atoms: Atoms):
    atoms.centre()

    with open(path / "CONFIG", "w+") as f:
        f.write("Frame :         1\n")
        f.write("\t0\t1\n")  # PBC Solution to temporary problem
        f.write(f"{GLOBALS.DLPOLY_CELL_SIZE} 0.0 0.0\n")
        f.write(f"0.0 {GLOBALS.DLPOLY_CELL_SIZE} 0.0\n")
        f.write(f"0.0 0.0 {GLOBALS.DLPOLY_CELL_SIZE}\n")
        for atom in atoms:
            f.write(
                f"{atom.type}  {atom.num}  {GLOBALS.SYSTEM_NAME}_{atom.type}{atom.num}\n"
            )
            f.write(f"{atom.x}\t\t{atom.y}\t\t{atom.z}\n")


def write_field(path: Path, atoms: Atoms):
    bonds, angles, dihedrals = get_internal_feature_indices(atoms)

    with open(path / "FIELD", "w") as f:
        f.write("DL_FIELD v3.00\n")
        f.write("Units kJ/mol\n")
        f.write("Molecular types 1\n")
        f.write(f"{GLOBALS.SYSTEM_NAME}\n")
        f.write("nummols 1\n")
        f.write(f"atoms {len(atoms)}\n")
        for atom in atoms:
            f.write(
                #  Atom Type      Atomic Mass                    Charge Repeats Frozen(0=NotFrozen)
                f"{atom.type}\t\t{dlpoly_weights[atom.type]:.7f}     0.0   1   0\n"
            )
        f.write(f"BONDS {len(bonds)}\n")
        for i, j in bonds:
            f.write(f"harm {i} {j} 0.0 0.0\n")
        if len(angles) > 0:
            f.write(f"ANGLES {len(angles)}\n")
            for i, j, k in angles:
                f.write(f"harm {i} {j} {k} 0.0 0.0\n")
        if len(dihedrals) > 0:
            f.write(f"DIHEDRALS {len(dihedrals)}\n")
            for i, j, k, l in dihedrals:
                f.write(f"harm {i} {j} {k} {l} 0.0 0.0\n")
        f.write("finish\n")
        f.write("close\n")


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
    gjfs = []
    for d in dlpoly_directory.iterdir():
        if d.is_dir() and (d / "HISTORY").exists():
            dlpoly_history = DlpolyHistory(d / "HISTORY")
            gjf = GJF(d / (d.name + GJF.filetype))
            gjf.atoms = dlpoly_history[-1]
            gjf.write()
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
