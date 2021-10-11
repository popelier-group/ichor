from ichor.main.amber import amber_menu
from ichor.make_sets import make_sets_menu
from ichor.menu import Menu


def md_menu() -> None:
    with Menu(
        "Molecular Dynamics Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option("amber", "Amber Menu", amber_menu)


def tools_menu() -> None:
    """Handler function which makes a new menu that contains useful tasks ICHOR can perform"""
    with Menu("Tools Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("m", "Make Sets Menu", make_sets_menu)
        menu.add_option("md", "Molecular Dynamics Tools", md_menu)
