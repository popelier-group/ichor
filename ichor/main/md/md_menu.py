from ichor.menu import Menu
from ichor.main.md.amber import amber_menu


def md_menu() -> None:
    with Menu(
        "Molecular Dynamics Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option("amber", "Amber Menu", amber_menu)