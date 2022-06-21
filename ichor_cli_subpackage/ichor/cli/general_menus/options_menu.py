from ichor.cli.general_menus.edit_globals_menu import settings_menu
from ichor.core.menu import Menu


def display_version():
    import ichor

    print(f"ICHOR Core: {ichor.core.__version__}")
    print(f"ICHOR HPC:  {ichor.hpc.__version__}")
    print(f"ICHOR CLI:  {ichor.cli.__version__}")


def options_menu() -> None:
    with Menu("Options Menu") as menu:
        menu.add_option("settings", "Settings Menu", settings_menu)
        menu.add_option(
            "version", "Display Version", display_version, wait=True
        )
