from typing import Optional
from pathlib import Path
import json
from ichor.common.io import pushd, mkdir

def collate_model_log(directory: Optional[Path] = None) -> None:
    from ichor.globals import GLOBALS
    from ichor.models import Models
    if directory is None:
        directory = GLOBALS.CWD

    with pushd(directory, update_cwd=True):
        if not GLOBALS.FILE_STRUCTURE["child_processes"].exists():
            return

        with open(GLOBALS.FILE_STRUCTURE["child_processes"], "r") as f:
            child_processes = json.load(f)

        parent_dir = Path(GLOBALS.CWD)
        parent_model_dir = parent_dir / GLOBALS.FILE_STRUCTURE["model_log"]
        mkdir(parent_model_dir)

        for child_process in child_processes:
            with pushd(child_process, update_cwd=True):
                for model_log in GLOBALS.FILE_STRUCTURE["model_log"].iterdir():
                    if model_log.is_dir() and Models.dirpattern.match(model_log.name):
                        cp(model_log, parent_model_dir / model_log.name)
