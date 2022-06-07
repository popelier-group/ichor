from ichor.cli.menus.general_menus.edit_globals_menu import settings_menu
from ichor.cli.menus.menu import Menu


def options_menu() -> None:
    with Menu("Options Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("settings", "Settings Menu", settings_menu)
