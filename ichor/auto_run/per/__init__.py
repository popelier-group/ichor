from ichor.menu import Menu
from ichor.auto_run.per.per_atom import auto_run_per_atom


def auto_run_per_atom_menu():
    with Menu("Per-Atom Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("r", "Run per-atom", auto_run_per_atom)
