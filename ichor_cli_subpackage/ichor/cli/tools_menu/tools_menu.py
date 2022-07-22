from ichor.cli.tools_menu.make_sets_menu import make_sets_menu
from ichor.cli.molecular_dynamics_menus import md_menu
from ichor.core.menu import Menu


def tools_menu():
    with Menu("Tools Menu") as menu:
        menu.add_option("m", "Make Sets Menu", make_sets_menu)
        menu.add_option("md", "Molecular Dynamics Menu", md_menu)
