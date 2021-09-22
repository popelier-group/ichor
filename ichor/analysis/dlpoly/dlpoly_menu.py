from pathlib import Path

from ichor.atoms import Atoms
from ichor.common.io import mkdir
from ichor.file_structure import FILE_STRUCTURE
from ichor.menu import Menu
from ichor.models import Models

_dlpoly_input_file = Path(".")
_model_location = Path(".")


def dlpoly_menu_refresh(menu: Menu):
    menu.clear_options()
    menu.add_option("1", "Run DLPOLY geometry optimisations on model(s)")
    menu.add_option("2", "Run DLPOLY fixed temperature run on model(s)")
    menu.add_space()
    menu.add_option("s", "Setup DLPOLY Directories", setup_dlpoly_directories)
    menu.add_option("g", "Run Gaussian on DLPOLY Output")
    menu.add_option("t", "Trajectory Analysis Tools")
    menu.add_space()
    menu.add_option("r", "Auto-Run Dlpoly Analysis")
    menu.add_space()
    menu.add_message(f"DLPOLY Input: {_dlpoly_input_file}")
    menu.add_message(f"Model Location: {_model_location}")


def dlpoly_menu():
    with Menu("DLPOLY Analysis Menu", refresh=dlpoly_menu_refresh):
        pass
