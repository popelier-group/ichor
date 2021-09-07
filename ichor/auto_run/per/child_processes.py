import json
from pathlib import Path
from typing import List, Optional

from ichor.common.io import pushd
from ichor.file_structure import FILE_STRUCTURE
from ichor.main.queue import delete_jobs


def find_child_processes_recursively(src: Path = Path.cwd()) -> List[Path]:
    child_processes = []
    if (src / FILE_STRUCTURE["child_processes"]).exists():
        with open(src / FILE_STRUCTURE["child_processes"], "r") as f:
            child_processes += json.load(f)

    for child_process in child_processes:
        child_processes += find_child_processes_recursively(child_process)

    child_processes = list(map(Path, child_processes))
    return child_processes


def delete_child_process_jobs(
    child_processes: Optional[List[Path]] = None,
) -> None:
    if child_processes is None:
        child_processes = find_child_processes_recursively()
    for child_process in child_processes:
        with pushd(child_process, update_cwd=True):
            delete_jobs()
