from pathlib import Path
from typing import List, Optional

from ichor.analysis import analysis_menu
from ichor.main.make_models import make_models_menu
from ichor.main.options_menu import options_menu
from ichor.main.qcp import submit_qcp
from ichor.main.qct import submit_qct
from ichor.main.queue import queue_menu
from ichor.main.tools_menu import tools_menu
from ichor.menu import Menu
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM
from ichor.qct import QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM

_points_directory_path = None


def _points_directory_menu_refresh(menu):
    from ichor.auto_run.standard_auto_run import auto_run_qct

    global _points_directory_path
    menu.clear_options()
    menu.add_option(
        "1",
        f"Submit Points to {QUANTUM_CHEMISTRY_PROGRAM().name}",
        submit_qcp,
        kwargs={
            "directory": _points_directory_path
        },  # which directory to submit gjfs from (TRAINING_SET, SAMPLE_POOL, etc.). Set by GLOBALS.FILE_STRUCTURE
    )
    menu.add_option(
        "2",
        f"Submit Points to {QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM().name}",
        submit_qct,
        kwargs={"directory": _points_directory_path},
    )
    menu.add_option(
        "3",
        "Make Models",
        make_models_menu,
        kwargs={"directory": _points_directory_path},
    )
    menu.add_space()
    menu.add_option(
        "a",
        f"Auto-Run {QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM().name}",
        auto_run_qct,
        kwargs={"directory": _points_directory_path},
    )
    menu.add_final_options()


def custom_points_directory_menu():
    from ichor.analysis.get_path import get_dir

    global _points_directory_path
    _points_directory_path = get_dir(Path())

    with Menu(
        f"{_points_directory_path} Menu",
        refresh=_points_directory_menu_refresh,
    ):
        pass


def points_directory_menu(path: Path):
    """Menu that shows up when the user wants to run jobs for a particular Points directory, such as the training set directory,
    validation set directory, or sample pool directory.

    :param path: A Path object to the directory for which the menu is about.
    """
    global _points_directory_path
    _points_directory_path = path

    with Menu(f"{path} Menu", refresh=_points_directory_menu_refresh):
        pass


def main_menu(subdirs: Optional[List[Path]] = None) -> None:
    """Initialize the main menu Command Line Interface (CLI) for ICHOR. Other menus can then be accessed from this main menu."""
    from ichor.auto_run.standard_auto_run import auto_run_from_menu
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.main.active_learning import active_learning
    from ichor.main.per_menu import auto_run_per_menu

    # initialize an instance of Menu called menu and add construct the menu in the context manager
    with Menu(
        "ICHOR Main Menu",
        enable_problems=True,
        space=True,
        back=False,
        exit=True,
        run_in_subdirectories=subdirs,
    ) as menu:
        # add options to the instance `menu`
        menu.add_option(
            "1",
            "Training Set Menu",
            # the handler function in this case is points_directory_menu. This function gets called when the user selects option 1 in the menu.
            points_directory_menu,
            # give key word arguments which are passed to the handler function
            kwargs={
                "path": FILE_STRUCTURE["training_set"]
            },  # get the Path of the training set from GLOBALS.FILE_STRUCTURE
        )
        menu.add_option(
            "2",
            "Sample Pool Menu",
            points_directory_menu,
            kwargs={"path": FILE_STRUCTURE["sample_pool"]},
        )
        menu.add_option(
            "3",
            "Validation Set Menu",
            points_directory_menu,
            kwargs={"path": FILE_STRUCTURE["validation_set"]},
        )
        menu.add_option(
            "4",
            "Active Learning",
            active_learning,
            kwargs={
                "model_directory": FILE_STRUCTURE["models"],
                "sample_pool_directory": FILE_STRUCTURE["sample_pool"],
            },
        )
        menu.add_space()  # add a blank line
        menu.add_option(
            "r",
            "Auto Run",
            auto_run_from_menu,
        )
        menu.add_option("p", "Per-Value Auto Run", auto_run_per_menu)
        menu.add_space()
        menu.add_option(
            "c", "Custom PointsDirectory Menu", custom_points_directory_menu
        )
        menu.add_option("a", "Analysis Menu", analysis_menu)
        menu.add_option("t", "Tools Menu", tools_menu)
        menu.add_option("o", "Options Menu", options_menu)
        menu.add_option("q", "Queue Menu", queue_menu)
