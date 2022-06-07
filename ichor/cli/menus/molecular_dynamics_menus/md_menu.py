from ichor.cli.menus.menu import Menu
from ichor.cli.menus.molecular_dynamics_menus.amber import amber_menu
from ichor.cli.menus.molecular_dynamics_menus.cp2k import cp2k_menu
from ichor.cli.menus.molecular_dynamics_menus.tyche import tyche_menu


def md_menu() -> None:
    with Menu(
        "Molecular Dynamics Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option("amber", "Amber Menu", amber_menu)
        menu.add_option("cp2k", "CP2K Menu", cp2k_menu)
        menu.add_option("tyche", "Tyche Menu", tyche_menu)
