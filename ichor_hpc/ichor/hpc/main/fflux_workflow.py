"""Submission of the Gaussian -> AIMAll -> SQLite FFLUX workflow."""

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, Union

import ichor.hpc.global_variables
from ichor.core.files import PointsDirectory
from ichor.hpc.batch_system import JobID
from ichor.hpc.main.aimall import submit_wfns
from ichor.hpc.main.database import submit_make_database
from ichor.hpc.main.gaussian import submit_gjfs, write_gjfs


@dataclass(frozen=True)
class FFLUXWorkflowJobs:
    """Paths and scheduler IDs produced by :func:`submit_fflux_workflow`."""

    points_directory: Path
    gaussian: Optional[JobID]
    aimall: Optional[JobID]
    database: Optional[JobID]


def submit_fflux_workflow(
    input_path: Union[str, Path, PointsDirectory],
    system_name: Optional[str] = None,
    every: int = 1,
    center: bool = True,
    gaussian_ncores: int = 2,
    aimall_ncores: int = 2,
    database_ncores: int = 1,
    method: str = "B3LYP",
    overwrite_existing_gjfs: bool = False,
    force_calculate_wfn: bool = False,
    force_calculate_ints: bool = False,
    gaussian_kwargs: Optional[Dict[str, Any]] = None,
    aimall_kwargs: Optional[Dict[str, Any]] = None,
) -> FFLUXWorkflowJobs:
    """Create/accept a points directory and submit three dependent jobs.

    ``input_path`` may be an existing ``.pointsdir`` directory or an XYZ
    trajectory.  Separate scripts are submitted for Gaussian, AIMAll, and
    database creation, so no single allocation spans the whole workflow.
    AIMAll is held for Gaussian and the database is held for AIMAll.
    """

    gaussian_kwargs = dict(gaussian_kwargs or {})
    aimall_kwargs = dict(aimall_kwargs or {})

    if isinstance(input_path, PointsDirectory):
        points = input_path
    else:
        input_path = Path(input_path)
        if input_path.is_dir():
            points = PointsDirectory(input_path)
        else:
            points = PointsDirectory.from_trajectory(
                input_path,
                system_name=system_name,
                every=every,
                center=center,
            )

    gaussian_kwargs.setdefault("method", method)
    gjfs = write_gjfs(points, overwrite_existing_gjfs, **gaussian_kwargs)
    expected_wfns = [gjf.with_suffix(".wfn") for gjf in gjfs]

    try:
        gaussian_job = submit_gjfs(
            gjfs,
            force_calculate_wfn=force_calculate_wfn,
            ncores=gaussian_ncores,
            script_name=ichor.hpc.global_variables.SCRIPT_NAMES["gaussian"],
        )
    except ValueError as error:
        if str(error) != "There are no jobs to submit in the submission script.":
            raise
        # All expected WFN files already exist and passed the current validation.
        gaussian_job = None
    aimall_job = submit_wfns(
        expected_wfns,
        force_calculate_ints=force_calculate_ints,
        ncores=aimall_ncores,
        hold=gaussian_job,
        method=method.upper().strip(),
        script_name=ichor.hpc.global_variables.SCRIPT_NAMES["aimall"],
        **aimall_kwargs,
    )
    database_job = submit_make_database(
        points.path,
        database_format="sqlite",
        ncores=database_ncores,
        hold=aimall_job,
        script_name=ichor.hpc.global_variables.SCRIPT_NAMES["pd_to_database"],
    )

    return FFLUXWorkflowJobs(points.path, gaussian_job, aimall_job, database_job)
