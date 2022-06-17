from ichor.cli.general_menus.edit_globals_menu import settings_menu
from ichor.core.menu import Menu


def options_menu() -> None:
    with Menu("Options Menu") as menu:
        menu.add_option("settings", "Settings Menu", settings_menu)
