from ichor.main.md.amber import amber_menu
from ichor.main.md.cp2k import cp2k_menu
from ichor.main.md.tyche import tyche_menu
from ichor.ichor_cli.menus.menu import Menu


def md_menu() -> None:
    with Menu(
        "Molecular Dynamics Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option("amber", "Amber Menu", amber_menu)
        menu.add_option("cp2k", "CP2K Menu", cp2k_menu)
        menu.add_option("tyche", "Tyche Menu", tyche_menu)
