import os
import json
from pathlib import Path
from typing import Any, Callable, List, Optional

from ichor.batch_system import JobID
from ichor.common.io import cp, get_files_of_type, mkdir, pushd

from ichor.auto_run.ichor import submit_collate_log


class TooManyXYZs(Exception):
    pass


def auto_run_per_value(
    variable: str,
    values: List[str],
    directory: Path = Path.cwd(),
    run_func: Optional[Callable] = None,
) -> List[Optional[JobID]]:
    from ichor.arguments import Arguments
    from ichor.globals import GLOBALS

    final_job_ids = []

    for value in values:
        path = directory / value
        mkdir(path)

        mkdir(GLOBALS.FILE_STRUCTURE["child_processes"].parent)
        child_processes = []
        if GLOBALS.FILE_STRUCTURE["child_processes"].exists():
            with open(GLOBALS.FILE_STRUCTURE["child_processes"], "w") as f:
                child_processes = json.load(f)
        child_processes.append(str(path.absolute()))
        with open(GLOBALS.FILE_STRUCTURE["child_processes"], "w") as f:
            json.dump(child_processes, f)

        if not (
            path / GLOBALS.FILE_STRUCTURE["training_set"]
        ).exists():  # No need to make training set if already exists
            if GLOBALS.FILE_STRUCTURE["training_set"].exists():
                cp(
                    GLOBALS.FILE_STRUCTURE["training_set"],
                    path / GLOBALS.FILE_STRUCTURE["training_set"],
                )  # need to copy as will be modified
                if GLOBALS.FILE_STRUCTURE["sample_pool"].exists():
                    cp(
                        GLOBALS.FILE_STRUCTURE["sample_pool"],
                        path / GLOBALS.FILE_STRUCTURE["sample_pool"],
                    )  # need to copy as will be modified
                if GLOBALS.FILE_STRUCTURE["validation_set"].exists():
                    (
                        path / GLOBALS.FILE_STRUCTURE["validation_set"]
                    ).symlink_to(
                        os.path.relpath(
                            GLOBALS.FILE_STRUCTURE["validation_set"],
                            start=path,
                        ),
                        target_is_directory=True,
                    )  # can be symlinked as all should be identical
            else:
                # todo: come up with better solution to find initial training set location
                xyzs = get_files_of_type(".xyz")
                if len(xyzs) == 0:
                    raise FileNotFoundError(
                        "Cannot find training set initialisation location, add xyz to directory"
                    )
                elif len(xyzs) > 1:
                    raise TooManyXYZs(
                        "Too many xyz files found, remove those that aren't required"
                    )
                (path / xyzs[0].name).symlink_to(
                    xyzs[0]
                )  # can symlink as xyz won't be modified

        if not (path / GLOBALS.FILE_STRUCTURE["programs"]).exists():
            (path / GLOBALS.FILE_STRUCTURE["programs"]).symlink_to(
                os.path.relpath(
                    GLOBALS.FILE_STRUCTURE["programs"], start=path
                ),
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
                from ichor.auto_run import auto_run

                final_job = auto_run()
                final_job_ids.append(final_job)
            else:
                final_jobs = run_func()
                final_job_ids.extend(final_jobs)

        GLOBALS.set(variable, save_value)
        Arguments.config_file = save_config

    final_job = submit_collate_log(GLOBALS.CWD, hold = final_job_ids)
    final_job_ids.append(final_job)

    return final_job_ids
