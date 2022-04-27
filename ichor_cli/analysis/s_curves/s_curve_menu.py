from pathlib import Path

from ichor.analysis.get_models import choose_model_menu, try_get_latest_models
from ichor.analysis.get_path import get_dir, get_generic_path
from ichor.analysis.get_validation_set import (
    choose_validation_set_menu, get_validation_set_from_current_dir)
from ichor.analysis.s_curves.compact_s_curves import calculate_compact_s_curves
from ichor.analysis.s_curves.s_curves import calculate_s_curves
from ichor.menus.menu import Menu

_validation_set_location = Path(".")
_model_location = Path(".")
_output_location = Path("s-curves.xlsx")

_compact_s_curves = True


def choose_model():
    global _model_location
    print("Enter Model Directory: ")
    _model_location = get_dir()


def choose_validation_set():
    global _validation_set_location
    print("Enter Validation Set Location: ")
    _validation_set_location = get_dir()


def choose_output_location():
    global _output_location
    _output_location = get_generic_path(
        prompt="Enter s-curves output: ", prefill=str(_output_location)
    )
    if _output_location.suffix != ".xlsx":
        _output_location = _output_location.with_suffix(".xlsx")


def toggle_compact_s_curves():
    global _compact_s_curves
    _compact_s_curves = not _compact_s_curves


def s_curve_menu_refresh(menu: Menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Calculate s-curves",
        calculate_compact_s_curves
        if _compact_s_curves
        else calculate_s_curves,
        kwargs={
            "model_location": _model_location,
            "validation_set_location": _validation_set_location,
            "output_location": _output_location,
        },
    )

    menu.add_space()
    menu.add_option("vs", "Choose Validation Set", choose_validation_set)
    menu.add_option("model", "Choose Model", choose_model)
    menu.add_option("output", "Choose Output Location", choose_output_location)
    menu.add_option(
        "compact", "Toggle Compact S-Curves", toggle_compact_s_curves
    )
    menu.add_space()
    menu.add_message(f"Validation Set Location: {_validation_set_location}")
    menu.add_message(f"Models Location: {_model_location}")
    menu.add_message(f"Output Location: {_output_location}")
    menu.add_message(f"Compact S-Curves: {_compact_s_curves}")
    menu.add_final_options()


def s_curve_menu():
    global _validation_set_location
    global _model_location
    from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE

    _validation_set_location = FILE_STRUCTURE["validation_set"]
    _model_location = FILE_STRUCTURE["models"]

    with Menu("S-Curve Analysis Menu", refresh=s_curve_menu_refresh):
        pass
