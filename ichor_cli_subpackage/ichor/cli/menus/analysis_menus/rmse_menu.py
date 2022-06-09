from pathlib import Path

from ichor.core.analysis.get_models import choose_model_menu
from ichor.core.analysis.get_validation_set import (
    choose_validation_set_menu,
    get_validation_set_from_current_dir,
)
from ichor.core.analysis.rmse.rmse import calculate_rmse
from ichor.core.menu import Menu, MenuVar
from ichor.hpc import FILE_STRUCTURE


def choose_model(model_location: MenuVar[Path]):
    model_location.var = choose_model_menu(model_location.var)


def choose_validation_set(validation_set_location: MenuVar[Path]):
    validation_set_location.var = choose_validation_set_menu(
        validation_set_location.var
    )


def rmse_menu():
    validation_set_location = MenuVar(
        "Validation Set Location", get_validation_set_from_current_dir()
    )
    model_location = MenuVar("Models Location", FILE_STRUCTURE["model_log"])

    with Menu("RMSE Analysis Menu") as menu:
        menu.add_option(
            "1",
            "Calculate RMSE",
            calculate_rmse,
            kwargs={
                "models_location": model_location,
                "validation_set_location": validation_set_location,
            },
        )
        menu.add_space()
        menu.add_option(
            "vs",
            "Choose Validation Set",
            choose_validation_set,
            args=[validation_set_location],
        )
        menu.add_option(
            "model", "Choose Model", choose_model, args=[model_location]
        )
        menu.add_space()
        menu.add_var(validation_set_location)
        menu.add_var(model_location)
