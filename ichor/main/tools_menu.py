from ichor.main.md import md_menu
from ichor.main.tools import revert_int_bak_menu
from ichor.main.tools.concatenate_points_directories import (
    concatenate_points_directories_menu,
)
from ichor.make_sets import make_sets_menu
from ichor.menu import Menu


def tools_menu() -> None:
    """Handler function which makes a new menu that contains useful tasks ICHOR can perform"""
    with Menu("Tools Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("m", "Make Sets Menu", make_sets_menu)
        menu.add_option("md", "Molecular Dynamics Tools", md_menu)
        menu.add_option(
            "concat",
            "Concatenate Points Directories",
            concatenate_points_directories_menu,
        )
        menu.add_option("bak", "Revert INT Backups", revert_int_bak_menu)
