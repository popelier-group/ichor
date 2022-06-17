from ichor.cli.menus.molecular_dynamics_menus.amber import amber_menu
from ichor.cli.menus.molecular_dynamics_menus.cp2k import cp2k_menu
from ichor.cli.menus.molecular_dynamics_menus.tyche import tyche_menu
from ichor.core.menu import Menu


def md_menu() -> None:
    with Menu("Molecular Dynamics Menu") as menu:
        menu.add_option("amber", "Amber Menu", amber_menu)
        menu.add_option("cp2k", "CP2K Menu", cp2k_menu)
        menu.add_option("tyche", "Tyche Menu", tyche_menu)
