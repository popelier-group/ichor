from pathlib import Path

from ichor.ichor_lib.analysis.get_path import get_dir
from ichor_hpc.file_structure.file_structure import FILE_STRUCTURE
from ichor.ichor_cli.menus.menu import Menu

_current_validation_set = None


def get_validation_set_from_current_dir():
    if FILE_STRUCTURE["validation_set"].exists():
        return FILE_STRUCTURE["validation_set"]
    return None


def set_validation_set(vs: Path) -> None:
    global _current_validation_set
    _current_validation_set = vs


def choose_custom_validation_set():
    set_validation_set(get_dir())


def choose_validation_set_menu_refresh(menu: Menu):
    menu.clear_options()
    menu.add_option(
        "1",
        f"{FILE_STRUCTURE['validation_set']}",
        set_validation_set,
        kwargs={"vs": FILE_STRUCTURE["validation_set"]},
    )
    menu.add_option(
        "2",
        f"{FILE_STRUCTURE['sample_pool']}",
        set_validation_set,
        kwargs={"vs": FILE_STRUCTURE["sample_pool"]},
    )
    menu.add_option(
        "3", f"Custom Validation Set Directory", choose_custom_validation_set
    )
    menu.add_space()
    menu.add_message(f"Current Validation Set: {_current_validation_set}")
    menu.add_final_options()


def choose_validation_set_menu(current_validation_set_directory: Path) -> Path:
    global _current_validation_set
    _current_validation_set = current_validation_set_directory
    with Menu(
        "Choose Validation Set Menu",
        refresh=choose_validation_set_menu_refresh,
        auto_close=True,
    ):
        pass
    return _current_validation_set
