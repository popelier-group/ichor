import json
import os
from pathlib import Path
from typing import Callable, List, Optional

from ichor.core.common.bool import check_bool
from ichor.core.common.io import cp, mkdir, pushd, relpath, remove
from ichor.hpc.auto_run.counter import (counter_exists, read_counter,
                                        remove_counter)
from ichor.hpc.auto_run.ichor_jobs import \
    submit_ichor_collate_log_job_to_auto_run
from ichor.hpc.batch_system import JobID
from ichor.hpc.points import get_points_location


def check_auto_run_per_counter(directory: Path, values: List[str]):
    directories = [directory / value for value in values]
    counter_file_exists = [
        counter_exists(directory) for directory in directories
    ]
    if any(counter_file_exists):
        print("Auto Run Counter File(s) Encountered:")
        for directory, exists in zip(directories, counter_file_exists):
            if exists:
                current_iter, max_iter = read_counter(directory)
                print(
                    f" - {directory} | Current Iter: {current_iter} | Max Iter: {max_iter}"
                )
        if check_bool(input("Would you like to delete counter files? [y/n] ")):
            for directory, exists in zip(directories, counter_file_exists):
                if exists:
                    remove_counter(directory)


def auto_run_per_value(
    variable: str,
    values: List[str],
    directory: Path = Path.cwd(),
    run_func: Optional[Callable] = None,
) -> List[Optional[JobID]]:
    """Returns a list of job ids which to submit

    :param variable: A string indicating which attribute of GLOBALS to access.
    :param values: which atoms or properties to run separate auto-run for.
    :param directory: The directory where to run the daemon, defaults to Path.cwd()
    :param run_func: An optional function to run, defaults to None.
        If no function is given, then the `ichor.auto_run.standard_auto_run.auto_run` function is ran
    :raises TypeError: [description]
    :return: A list of job ids which are going to run on compute nodes
    """

    from ichor.hpc import FILE_STRUCTURE, GLOBALS
    from ichor.hpc.arguments import Arguments

    check_auto_run_per_counter(directory, values)

    final_job_ids = []

    # iterate over atom names
    for value in values:

        # make a separate directory for every atom in which to do auto run
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

                if (path / points_location.name).exists():
                    remove(path / points_location.name)

                (path / points_location.name).symlink_to(
                    relpath(points_location, path)
                )  # can symlink as xyz won't be modified

        # if not (path / FILE_STRUCTURE["programs"]).exists():
        #     (path / FILE_STRUCTURE["programs"]).symlink_to(
        #         os.path.relpath(FILE_STRUCTURE["programs"], start=path),
        #         target_is_directory=True,
        #     )

        save_config = Arguments.config_file
        save_value = GLOBALS.get(variable)

        config_path = str((path / "config.properties").absolute())
        Arguments.config_file = config_path
        GLOBALS.set(variable, value)
        GLOBALS.save_to_config(config_path)

        with pushd(path, update_cwd=True):
            if run_func is None:
                from ichor.hpc.auto_run.standard_auto_run import auto_run

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
