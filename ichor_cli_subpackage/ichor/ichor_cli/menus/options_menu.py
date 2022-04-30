from ichor.ichor_cli.menus.menu import Menu


def options_menu() -> None:
    from ichor.globals import settings_menu

    with Menu("Options Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("settings", "Settings Menu", settings_menu)
