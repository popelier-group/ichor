import itertools
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ichor.common.io import cp, mkdir, pushd
from ichor.common.types import DictList


def get_child_processes() -> Optional[List[Path]]:
    from ichor.file_structure import FILE_STRUCTURE

    if not FILE_STRUCTURE["child_processes"].exists():
        from ichor.auto_run.per.child_processes import \
            find_child_processes_recursively

        find_child_processes_recursively()
        if not FILE_STRUCTURE["child_processes"].exists():
            return

    with open(FILE_STRUCTURE["child_processes"], "r") as f:
        return list(map(Path, set(json.load(f))))


def get_collate_model_log(
    directory: Optional[Path] = None,
) -> Dict[str, Dict[str, Tuple[Path, int]]]:
    from ichor.common.types import DictList
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS
    from ichor.models import Models

    if directory is None:
        directory = GLOBALS.CWD

    with pushd(directory, update_cwd=True):
        if not FILE_STRUCTURE["model_log"].exists():
            collate_model_log()
        if not FILE_STRUCTURE["model_log"].exists():
            return {}

        collated_models = {}

        for d in FILE_STRUCTURE["model_log"].iterdir():
            if d.is_dir() and Models.check_path(d):
                models = Models(d)
                for model in models:
                    model.read(up_to="number_of_training_points")
                    if model.atom not in collated_models.keys():
                        collated_models[model.atom] = DictList()
                    collated_models[model.atom][model.type] += [(model.path, model.ntrain)]
        return collated_models


def link_collated_models(dir, collated_models):
    from ichor.common.io import ln
    from ichor.globals import GLOBALS

    mkdir(dir)
    for i, models in enumerate(collated_models):
        model_dir = dir / (
            GLOBALS.SYSTEM_NAME + "_MODELS" + str(i + 1).zfill(4)
        )
        mkdir(model_dir, empty=True)
        for model in models:
            if model is not None:
                ln(model.absolute(), model_dir / model.name)


def collate_model_log_bottom_up(directory: Optional[Path] = None):
    from ichor.file_structure import FILE_STRUCTURE

    collated_models = get_collate_model_log(directory)
    sorted_models = [(
            [m[0] for m in sorted(models, key=lambda x: x[1])] for models in types
        ) for atom, types in collated_models.items()]
    sorted_models = list(
        map(list, itertools.zip_longest(*sorted_models, fillvalue=None))
    )
    link_collated_models(
        FILE_STRUCTURE["model_log_collated_bottom_up"], sorted_models
    )


def collate_model_log_top_down(directory: Optional[Path] = None):
    from ichor.file_structure import FILE_STRUCTURE

    collated_models = get_collate_model_log(directory)
    sorted_models = [
        (
            [m[0] for m in sorted(models, key=lambda x: x[1], reverse=True)]
            for models in types
        )
        for atom, types in collated_models.items()
    ]

    sorted_models = list(
        reversed(
            list(
                map(
                    list, itertools.zip_longest(*sorted_models, fillvalue=None)
                )
            )
        )
    )
    link_collated_models(
        FILE_STRUCTURE["model_log_collated_top_down"], sorted_models
    )


def collate_model_log(directory: Optional[Path] = None) -> None:
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS
    from ichor.models import Models

    if directory is None:
        directory = GLOBALS.CWD

    with pushd(directory, update_cwd=True):
        child_processes = get_child_processes()
        if child_processes is None:
            return

        parent_dir = Path(GLOBALS.CWD)
        parent_model_dir = parent_dir / FILE_STRUCTURE["model_log"]
        mkdir(parent_model_dir)

        for child_process in child_processes:
            with pushd(child_process, update_cwd=True):
                for model_log in FILE_STRUCTURE["model_log"].iterdir():
                    if model_log.is_dir() and Models.check_path(model_log):
                        new_model_loc = parent_model_dir / model_log.name
                        mkdir(new_model_loc)
                        cp(model_log, new_model_loc)
    collate_model_log_bottom_up(directory)
    collate_model_log_top_down(directory)


def collate_models(directory: Optional[Path] = None) -> None:
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS

    if directory is None:
        directory = GLOBALS.CWD

    with pushd(directory, update_cwd=True):
        child_processes = get_child_processes()
        if child_processes is None:
            return

        parent_dir = Path(GLOBALS.CWD)
        parent_model_dir = parent_dir / FILE_STRUCTURE["models"]
        mkdir(parent_model_dir)

        for child_process in child_processes:
            with pushd(child_process, update_cwd=True):
                if FILE_STRUCTURE["models"].exists():
                    for f in FILE_STRUCTURE["models"].iterdir():
                        cp(f, parent_model_dir)
