from pathlib import Path

from ichor.analysis.dlpoly.dlpoly_analysis import (
    run_dlpoly, run_dlpoly_geometry_optimisations, setup_dlpoly_directories,
    submit_final_geometry_to_gaussian)
from ichor.analysis.dlpoly.dlpoly_submit import \
    submit_dlpoly_optimisation_analysis_auto_run
from ichor.analysis.get_input import get_first_file, get_input_menu
from ichor.analysis.get_path import get_dir
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import GJF, XYZ
from ichor.globals import GLOBALS
from ichor.menus.menu import Menu

_dlpoly_input_file = Path(".")
_model_location = Path(".")


def trajectory_analysis_menu_refresh(menu):
    menu.clear_options()
    menu.add_final_options()


def trajectory_analysis_menu():
    with Menu(
        "DLPOLY Trajectory Analysis Menu",
        refresh=trajectory_analysis_menu_refresh,
    ):
        pass


def _set_dlpoly_input():
    global _dlpoly_input_file
    _dlpoly_input_file = get_input_menu(
        _dlpoly_input_file, [XYZ.filetype, GJF.filetype]
    )


def _set_model_location():
    global _model_location
    _model_location = get_dir()


def dlpoly_menu_refresh(menu: Menu):
    menu.clear_options()
    menu.add_option(
        "1",
        "Run DLPOLY geometry optimisations on model(s)",
        run_dlpoly_geometry_optimisations,
        kwargs={
            "dlpoly_input": _dlpoly_input_file,
            "model_location": _model_location,
        },
    )
    menu.add_option(
        "2",
        "Run DLPOLY fixed temperature run on model(s)",
        run_dlpoly,
        kwargs={
            "dlpoly_input": _dlpoly_input_file,
            "model_location": _model_location,
            "temperature": GLOBALS.DLPOLY_TEMPERATURE,
        },
    )
    menu.add_space()
    menu.add_option(
        "s",
        "Setup DLPOLY Directories",
        setup_dlpoly_directories,
        kwargs={
            "dlpoly_input": _dlpoly_input_file,
            "model_location": _model_location,
        },
    )
    menu.add_option(
        "g", "Run Gaussian on DLPOLY Output", submit_final_geometry_to_gaussian
    )
    menu.add_option("t", "Trajectory Analysis Tools", trajectory_analysis_menu)
    menu.add_space()
    menu.add_option(
        "r",
        "Auto-Run Dlpoly Optimisation Analysis",
        submit_dlpoly_optimisation_analysis_auto_run,
        kwargs={
            "dlpoly_input": _dlpoly_input_file,
            "model_location": _model_location,
        },
    )
    menu.add_space()
    menu.add_option("i", "Select DLPOLY Input", _set_dlpoly_input)
    menu.add_option("m", "Select Model Input", _set_model_location)
    menu.add_space()
    menu.add_message(f"DLPOLY Input: {_dlpoly_input_file}")
    menu.add_message(f"Model Location: {_model_location}")
    menu.add_final_options()


def dlpoly_menu():
    global _dlpoly_input_file
    global _model_location

    # _dlpoly_input_file = get_first_file(
    #    FILE_STRUCTURE["validation_set"], [GJF.filetype], recursive=True
    # )
    _model_location = FILE_STRUCTURE["model_log"]

    with Menu("DLPOLY Analysis Menu", refresh=dlpoly_menu_refresh):
        pass
