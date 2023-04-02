from ichor.cli.general_menus.edit_globals_menu import settings_menu
from ichor.core.menu import Menu


def display_version():
    import ichor

    print(f"ICHOR Core: {ichor.core.__version__}")
    print(f"ICHOR HPC:  {ichor.hpc.__version__}")
    print(f"ICHOR CLI:  {ichor.cli.__version__}")


def display_machine():
    from ichor.hpc import MACHINE

    title = f"Machine Name: {MACHINE.name}"
    print("+" + "-"*(len(title)+2) + "+")
    print("| " + title + " |")
    print("+" + "-"*(len(title)+2) + "+")
    print(f"Address: {MACHINE.address}")
    print(f"Submit on Compute Available: {MACHINE.submit_on_compute}")
    print(f"Drop Compute Available: {MACHINE.drop_compute_available}")
    print(f"Submit Type: {MACHINE.submit_type.name}")


def options_menu() -> None:
    with Menu("Options Menu") as menu:
        menu.add_option("settings", "Settings Menu", settings_menu)
        menu.add_option(
            "version", "Display Version", display_version, wait=True
        )
        menu.add_option(
            "machine", "Display Machine Info", display_machine, wait=True
        )
