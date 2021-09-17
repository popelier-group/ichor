from pathlib import Path

from ichor.analysis.get_path import get_dir
from ichor.file_structure import FILE_STRUCTURE
from ichor.menu import Menu

_current_validation_set = None


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


def choose_validation_set_menu(current_validation_set: Path) -> Path:
    global _current_validation_set
    _current_validation_set = current_validation_set
    with Menu(
        "Choose Validation Set Menu",
        refresh=choose_validation_set_menu_refresh,
        auto_close=True,
    ):
        pass
    return _current_validation_set
