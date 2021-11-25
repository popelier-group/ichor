import json
import os
from pathlib import Path
from typing import Callable, List, Optional

from ichor.auto_run.ichor_jobs import submit_ichor_collate_log_job_to_auto_run
from ichor.batch_system import JobID
from ichor.common.io import cp, mkdir, pushd, relpath
from ichor.common.points import get_points_location


def auto_run_per_value(
    variable: str,
    values: List[str],
    directory: Path = Path.cwd(),
    run_func: Optional[Callable] = None,
) -> List[Optional[JobID]]:
    from ichor.arguments import Arguments
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS

    final_job_ids = []

    for value in values:
        path = directory / value
        mkdir(path)

        mkdir(FILE_STRUCTURE["child_processes"].parent)
        child_processes = []
        if FILE_STRUCTURE["child_processes"].exists():
            with open(FILE_STRUCTURE["child_processes"], "r") as f:
                child_processes = json.load(f)
        child_processes.append(str(path.absolute()))
        child_processes = list(set(child_processes))
        with open(FILE_STRUCTURE["child_processes"], "w") as f:
            json.dump(child_processes, f)

        if not (
            path / FILE_STRUCTURE["training_set"]
        ).exists():  # No need to make training set if already exists
            if FILE_STRUCTURE["training_set"].exists():
                cp(
                    FILE_STRUCTURE["training_set"],
                    path / FILE_STRUCTURE["training_set"],
                )  # need to copy as will be modified
                if FILE_STRUCTURE["sample_pool"].exists():
                    cp(
                        FILE_STRUCTURE["sample_pool"],
                        path / FILE_STRUCTURE["sample_pool"],
                    )  # need to copy as will be modified
                if FILE_STRUCTURE["validation_set"].exists():
                    (path / FILE_STRUCTURE["validation_set"]).symlink_to(
                        os.path.relpath(
                            FILE_STRUCTURE["validation_set"],
                            start=path,
                        ),
                        target_is_directory=True,
                    )  # can be symlinked as all should be identical
            else:
                points_location = get_points_location()

                if points_location.suffix != ".xyz":
                    raise TypeError("Cannot find xyz for make sets")

                (path / points_location.name).symlink_to(
                    relpath(points_location, path)
                )  if not (path / points_location.name).exists() # can symlink as xyz won't be modified

        if not (path / FILE_STRUCTURE["programs"]).exists():
            (path / FILE_STRUCTURE["programs"]).symlink_to(
                os.path.relpath(FILE_STRUCTURE["programs"], start=path),
                target_is_directory=True,
            )

        save_config = Arguments.config_file
        save_value = GLOBALS.get(variable)

        config_path = str((path / "config.properties").absolute())
        Arguments.config_file = config_path
        GLOBALS.set(variable, value)
        GLOBALS.save_to_config(config_path)

        with pushd(path, update_cwd=True):
            if run_func is None:
                from ichor.auto_run.standard_auto_run import auto_run

                final_job = auto_run()
                final_job_ids.append(final_job)
            else:
                final_jobs = run_func()
                final_job_ids.extend(final_jobs)

        GLOBALS.set(variable, save_value)
        Arguments.config_file = save_config

    final_job = submit_ichor_collate_log_job_to_auto_run(
        GLOBALS.CWD, hold=final_job_ids
    )
    final_job_ids.append(final_job)

    return final_job_ids
