from pathlib import Path
from typing import Optional

from ichor.cli.menus.machine_learning_menus.make_models import make_models_menu
from ichor.core.menu import Menu, MenuVar, toggle_bool_var
from ichor.hpc.auto_run.standard_auto_run import auto_run_qct
from ichor.hpc.main.qcp import submit_qcp
from ichor.hpc.main.qct import submit_qct
from ichor.hpc.programs.qcp import QUANTUM_CHEMISTRY_PROGRAM
from ichor.hpc.programs.qct import QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM


def _toggle_force(force: MenuVar):
    force.var = not force.var


def custom_points_directory_menu():
    from ichor.core.analysis.get_path import get_dir

    points_directory_menu(get_dir(Path()))


def points_directory_menu(path: Path, title: Optional[str] = None):
    """Menu that shows up when the user wants to run jobs for a particular Points directory, such as the training set directory,
    validation set directory, or sample pool directory.

    Parameters
    ----------
    path: A Path object to the directory for which the menu is about.
    title: Optional str for title of menu
    """
    points_directory_path = MenuVar("Points Directory", path)
    force = MenuVar("Force", False)

    title = title or f"{points_directory_path.var} Menu"
    with Menu(title) as menu:
        menu.add_option(
            "1",
            f"Submit Points to {QUANTUM_CHEMISTRY_PROGRAM().name}",
            submit_qcp,
            args=[
                points_directory_path,
                force,
            ],  # which directory to submit gjfs from (TRAINING_SET, SAMPLE_POOL, etc.). Set by GLOBALS.FILE_STRUCTURE
        )
        menu.add_option(
            "2",
            f"Submit Points to {QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM().name}",
            submit_qct,
            args=[points_directory_path, force],
        )
        menu.add_option(
            "3",
            "Make Models",
            make_models_menu,
            args=[points_directory_path],
            # debug=True,
        )
        menu.add_space()
        menu.add_option(
            "a",
            f"Auto-Run {QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM().name}",
            auto_run_qct,
            args=[points_directory_path, force],
        )
        menu.add_option("f", "Toggle Force", toggle_bool_var, args=[force])
        menu.add_space()
        menu.add_var(force)
