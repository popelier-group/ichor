import json
from pathlib import Path
from typing import List, Optional

from ichor.auto_run import rerun_from_failed
from ichor.auto_run.stop import stop
from ichor.common.io import mkdir, pushd
from ichor.common.os import kill_pid, pid_exists
from ichor.daemon import Daemon
from ichor.file_structure import FILE_STRUCTURE
from ichor.main.queue import delete_jobs


def find_child_processes_recursively(src: Path = Path.cwd()) -> List[Path]:
    child_processes = []

    cp_dir = None
    if (src / FILE_STRUCTURE["child_processes"]).exists():
        with open(src / FILE_STRUCTURE["child_processes"], "r") as f:
            child_processes += json.load(f)
    elif (src / FILE_STRUCTURE["atoms"]).exists():
        cp_dir = src / FILE_STRUCTURE["atoms"]
    elif (src / FILE_STRUCTURE["properties"]).exists():
        cp_dir = src / FILE_STRUCTURE["properties"]

    if cp_dir is not None:
        for d in cp_dir.iterdir():
            if d.is_dir() and (d / FILE_STRUCTURE["data"]).exists():
                child_processes += [d]
        child_processes = [str(cp.absolute()) for cp in child_processes]
        with open(src / FILE_STRUCTURE["child_processes"], "w") as f:
            json.dump(child_processes, f)

    for child_process in child_processes:
        child_processes += find_child_processes_recursively(
            Path(child_process)
        )

    child_processes = list(set(map(Path, child_processes)))
    return child_processes


def delete_child_process_jobs(
    child_processes: Optional[List[Path]] = None,
) -> None:
    if child_processes is None:
        child_processes = find_child_processes_recursively()
    for child_process in child_processes:
        with pushd(child_process, update_cwd=True):
            delete_jobs()
            stop()


class ReRunDaemon(Daemon):
    def __init__(self):
        from ichor.file_structure import FILE_STRUCTURE
        from ichor.globals import GLOBALS

        mkdir(FILE_STRUCTURE["rerun_daemon"])
        pidfile = GLOBALS.CWD / FILE_STRUCTURE["rerun_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["rerun_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["rerun_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        rerun_failed_child_process()
        self.stop()


def rerun_failed_child_process(
    child_processes: Optional[List[Path]] = None,
) -> None:
    if child_processes is None:
        child_processes = find_child_processes_recursively()
    for child_process in child_processes:
        # todo: ensure finished
        with pushd(child_process, update_cwd=True):
            rerun_from_failed()


def stop_all_child_processes(
    child_processes: Optional[List[Path]] = None,
) -> None:
    if child_processes is None:
        child_processes = find_child_processes_recursively()

    with open(FILE_STRUCTURE["pids"], "r") as f:
        for line in f:
            pid = int(line)
            if pid_exists(pid):
                kill_pid(pid)

    delete_child_process_jobs(child_processes)


def print_child_process_status(cpdir: Path):
    from ichor.auto_run.counter import read_counter
    from ichor.common.io import pushd
    from ichor.file_structure import FILE_STRUCTURE

    with pushd(cpdir, update_cwd=True):
        print(f"{cpdir} Status")
        if FILE_STRUCTURE["counter"].exists():
            current_iteration, max_iteration = read_counter()
            print(f"Iteration {current_iteration} of {max_iteration}")
        else:
            print("No Counter File Found, Child Process May Have Finished")

        from ichor.common.io import last_modified
        from ichor.log import logger

        logger_path = Path(logger.root.handlers[0].baseFilename)
        print(f"{logger_path} last modified: {last_modified(logger_path)}")


def print_child_processes_status(child_processes: Optional[List[Path]] = None):
    if child_processes is None:
        child_processes = find_child_processes_recursively()
    for cp in child_processes:
        print_child_process_status(cp)


def concat_dir_to_ts(child_processes: Optional[List[Path]] = None):
    from ichor.analysis.get_path import get_dir
    from ichor.main.tools.concatenate_points_directories import \
        concatenate_points_directories

    print("Enter PointsDirectory Location to concatenate to training sets: ")
    dir = get_dir().absolute()
    if child_processes is None:
        child_processes = find_child_processes_recursively()

    for cp in child_processes:
        with pushd(cp, update_cwd=True):
            ts = cp / FILE_STRUCTURE["training_set"]
            if ts.exists():
                concatenate_points_directories(ts, dir, verbose=True)
