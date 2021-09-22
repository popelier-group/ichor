from pathlib import Path
from typing import List, Optional

from ichor.analysis.get_models import get_models_from_path
from ichor.batch_system import JobID
from ichor.file_structure import FILE_STRUCTURE
from ichor.submission_script import (SCRIPT_NAMES, DataLock, DlpolyCommand,
                                     ICHORCommand, SubmissionScript)
from ichor.submission_script.common import submit_gjf_files


def submit_setup_dlpoly_directories(
    dlpoly_input: Path,
    model_location: Path,
    dlpoly_directories: List[Path],
    hold: Optional[JobID] = None,
) -> JobID:
    with SubmissionScript(
        SCRIPT_NAMES["ichor"]["dlpoly"]["setup"]
    ) as submission_script:
        submission_script.add_command(
            ICHORCommand(
                func="run_dlpoly",
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
                func="submit_final_geometry_to_gaussian",
                func_args=[str(dlpoly_directory)],
            )
        )
    return submission_script.submit(hold=hold)


def submit_dlpoly_auto_run(
    dlpoly_input: Path,
    model_location: Path,
    dlpoly_directory: Path = FILE_STRUCTURE["dlpoly"],
    hold: Optional[JobID] = None,
) -> JobID:
    ninputs = len(get_models_from_path(model_location))
    dummy_paths = [Path("tmp.file") for _ in range(ninputs)]
    with DataLock():
        job_id = submit_setup_dlpoly_directories(
            dlpoly_input, model_location, dummy_paths, hold=hold
        )
        job_id = submit_dlpoly_jobs(dummy_paths, hold=hold)
        job_id = submit_write_dlpoly_gjfs(
            dlpoly_directory, dummy_paths, hold=hold
        )
        job_id = submit_dlpoly_gjfs(dummy_paths, hold=hold)
