from pathlib import Path

from ichor.analysis.get_models import choose_model_menu, try_get_latest_models
from ichor.analysis.get_validation_set import (
    choose_validation_set_menu, get_validation_set_from_current_dir)
from ichor.analysis.rmse.rmse import calculate_rmse
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.menus.menu import Menu

_validation_set_location = Path(".")
_model_location = Path(".")


def choose_model():
    global _model_location
    _model_location = choose_model_menu(_model_location)


def choose_validation_set():
    global _validation_set_location
    _validation_set_location = choose_validation_set_menu(
        _validation_set_location
    )


def rmse_menu_refresh(menu: Menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Calculate RMSE",
        calculate_rmse,
        kwargs={
            "models_location": _model_location,
            "validation_set_location": _validation_set_location,
        },
    )
    menu.add_space()
    menu.add_option("vs", "Choose Validation Set", choose_validation_set)
    menu.add_option("model", "Choose Model", choose_model)
    menu.add_space()
    menu.add_message(f"Validation Set Location: {_validation_set_location}")
    menu.add_message(f"Models Location: {_model_location}")
    menu.add_final_options()


def rmse_menu():
    global _validation_set_location
    global _model_location

    _validation_set_location = get_validation_set_from_current_dir()
    _model_location = FILE_STRUCTURE["model_log"]

    with Menu("RMSE Analysis Menu", refresh=rmse_menu_refresh):
        pass
