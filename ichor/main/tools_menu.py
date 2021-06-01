from ichor.make_sets import make_sets_menu
from ichor.menu import Menu


def tools_menu() -> None:
    with Menu("Tools Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("m", "Make Sets Menu", make_sets_menu)
