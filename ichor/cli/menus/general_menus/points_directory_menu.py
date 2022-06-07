from pathlib import Path

from ichor.cli.menus.machine_learning_menus.make_models import make_models_menu
from ichor.cli.menus.menu import Menu
from ichor.hpc.main.qcp import submit_qcp
from ichor.hpc.main.qct import submit_qct
from ichor.hpc.programs.qcp import QUANTUM_CHEMISTRY_PROGRAM
from ichor.hpc.programs.qct import QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM

_points_directory_path = None


def _toggle_force():
    global _force
    _force = not _force


def _points_directory_menu_refresh(menu):
    from ichor.hpc.auto_run.standard_auto_run import auto_run_qct

    global _points_directory_path

    menu.clear_options()
    menu.add_option(
        "1",
        f"Submit Points to {QUANTUM_CHEMISTRY_PROGRAM().name}",
        submit_qcp,
        kwargs={
            "directory": _points_directory_path,
            "force": _force,
        },  # which directory to submit gjfs from (TRAINING_SET, SAMPLE_POOL, etc.). Set by GLOBALS.FILE_STRUCTURE
    )
    menu.add_option(
        "2",
        f"Submit Points to {QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM().name}",
        submit_qct,
        kwargs={"directory": _points_directory_path, "force": _force},
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
        kwargs={"directory": _points_directory_path, "force": _force},
    )
    menu.add_option("f", "Toggle Force", _toggle_force)
    menu.add_space()
    menu.add_message(f"Force: {_force}")
    menu.add_final_options()


def custom_points_directory_menu():
    from ichor.core.analysis.get_path import get_dir

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
