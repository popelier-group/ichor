from pathlib import Path
from typing import List, Optional

from ichor.ichor_lib.analysis.get_path import get_dir
from ichor.ichor_lib.common.io import get_files_of_type
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.menus.menu import Menu
from ichor.models import Model, Models


class ModelsNotFound(Exception):
    pass


def number_of_models_in_dir(path: Path) -> int:
    return len(get_files_of_type(Model.filetype, path)) if path.exists() else 0


def get_latest_models_from_log() -> Path:
    if FILE_STRUCTURE["model_log"].exists():
        largest_ntrain = -1
        largest_model_found = None
        for model_dir in FILE_STRUCTURE["model_log"].iterdir():
            if number_of_models_in_dir(model_dir) > 0:
                if Models(model_dir).ntrain > largest_ntrain:
                    largest_model_found = model_dir
        if largest_model_found is not None:
            return largest_model_found
    raise ModelsNotFound()


def get_latest_models() -> Path:
    if (
        FILE_STRUCTURE["models"].exists()
        and number_of_models_in_dir(FILE_STRUCTURE["models"]) > 0
    ):
        return FILE_STRUCTURE["models"]
    else:
        return get_latest_models_from_log()


_current_model = None


def set_current_model(model: Path):
    global _current_model
    _current_model = model


def select_from_log():
    i = 1
    with Menu(
        "Select Model From Log", space=True, back=True, exit=True
    ) as menu:
        for model_dir in FILE_STRUCTURE["model_log"]:
            if number_of_models_in_dir(model_dir) > 0:
                menu.add_option(
                    f"{i}",
                    f"{model_dir}",
                    set_current_model,
                    kwargs={"model": model_dir},
                )
                i += 1


def enter_custom_directory():
    set_current_model(get_dir())


def choose_model_menu_refresh(menu: Menu):
    latest_model_from_log = try_get_latest_models_from_log()
    menu.clear_options()
    menu.add_option(
        "1",
        f"Latest FEREBUS Model: {FILE_STRUCTURE['models']}",
        set_current_model,
        kwargs={"model": FILE_STRUCTURE["models"]},
    )
    menu.add_option(
        "2",
        f"Latest Model From Log: {latest_model_from_log}",
        set_current_model,
        kwargs={"model": latest_model_from_log},
    )
    menu.add_option("3", f"Choose Model From Log", select_from_log)
    menu.add_option("4", "Custom Model Directory", enter_custom_directory)
    menu.add_space()
    menu.add_message(f"Current Model: {_current_model}")
    menu.add_final_options()


def choose_model_menu(current_model: Path) -> Path:
    global _current_model
    _current_model = current_model
    with Menu(
        "Choose Model Menu", refresh=choose_model_menu_refresh, auto_close=True
    ):
        pass
    return _current_model


def get_models_from_path(path: Path) -> List[Models]:
    """
    Get list of 'Models' instances from 'path'
    :param path: the path to search for instances of 'Models'
    :return: list of 'Models' from path
    :raises: ModelsNotFound if no models are found
    """
    if path.is_dir():
        if len(get_files_of_type(Model.filetype, path)) > 0:
            return [Models(path)]
        else:
            models = []
            for d in path.iterdir():
                if d.is_dir() and number_of_models_in_dir(d) > 0:
                    models += [Models(d)]
            if len(models) > 0:
                return models

    raise ModelsNotFound(f"No models found from '{path}")


def try_get_latest_models() -> Optional[Path]:
    try:
        return get_latest_models()
    except ModelsNotFound:
        return None


def try_get_models_from_path(path: Path) -> Optional[List[Models]]:
    try:
        return get_models_from_path(path)
    except ModelsNotFound:
        return None


def try_get_latest_models_from_log() -> Optional[Path]:
    try:
        return get_latest_models_from_log()
    except ModelsNotFound:
        return None
