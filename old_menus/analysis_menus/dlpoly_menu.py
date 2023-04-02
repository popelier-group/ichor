from pathlib import Path

from ichor.core.analysis.get_input import get_first_file, get_input_menu
from ichor.core.analysis.get_path import get_dir
from ichor.core.files import GJF, XYZ
from ichor.core.menu import Menu, MenuVar
from ichor.hpc import FILE_STRUCTURE, GLOBALS
from ichor.hpc.dlpoly_analysis.dlpoly_submit import (
    run_dlpoly, run_dlpoly_geometry_optimisations, setup_dlpoly_directories,
    submit_dlpoly_optimisation_analysis_auto_run,
    submit_final_geometry_to_gaussian)


def trajectory_analysis_menu():
    with Menu(
        "DLPOLY Trajectory Analysis Menu",
    ):
        # todo: add DLPOLY trajectory analysis
        pass


def _set_dlpoly_input(dlpoly_input_file: MenuVar):
    dlpoly_input_file.var = get_input_menu(
        dlpoly_input_file.var, [XYZ.filetype, GJF.filetype]
    )


def _set_model_location(model_location: MenuVar):
    model_location.var = get_dir()


def dlpoly_menu():
    dlpoly_input_file = MenuVar("DLPOLY Input", Path("."))
    model_location = MenuVar("Model Location", FILE_STRUCTURE["model_log"])

    with Menu("DLPOLY Analysis Menu") as menu:
        menu.add_option(
            "1",
            "Run DLPOLY geometry optimisations on model(s)",
            run_dlpoly_geometry_optimisations,
            kwargs={
                "dlpoly_input": dlpoly_input_file,
                "model_location": model_location,
            },
        )
        menu.add_option(
            "2",
            "Run DLPOLY fixed temperature run on model(s)",
            run_dlpoly,
            kwargs={
                "dlpoly_input": dlpoly_input_file,
                "model_location": model_location,
                "temperature": GLOBALS.DLPOLY_TEMPERATURE,
            },
        )
        menu.add_space()
        menu.add_option(
            "s",
            "Setup DLPOLY Directories",
            setup_dlpoly_directories,
            kwargs={
                "dlpoly_input": dlpoly_input_file,
                "model_location": model_location,
            },
        )
        menu.add_option(
            "g",
            "Run Gaussian on DLPOLY Output",
            submit_final_geometry_to_gaussian,
        )
        menu.add_option(
            "t", "Trajectory Analysis Tools", trajectory_analysis_menu
        )
        menu.add_space()
        menu.add_option(
            "r",
            "Auto-Run Dlpoly Optimisation Analysis",
            submit_dlpoly_optimisation_analysis_auto_run,
            kwargs={
                "dlpoly_input": dlpoly_input_file,
                "model_location": model_location,
            },
        )
        menu.add_space()
        menu.add_option(
            "i",
            "Select DLPOLY Input",
            _set_dlpoly_input,
            args=[dlpoly_input_file],
        )
        menu.add_option(
            "m",
            "Select Model Input",
            _set_model_location,
            args=[model_location],
        )
        menu.add_space()
        menu.add_var(dlpoly_input_file)
        menu.add_var(model_location)
