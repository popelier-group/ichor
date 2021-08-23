from ichor.auto_run.per import (PerAtomDaemon, PerAtomPerPropertyDaemon,
                                PerPropertyDaemon, auto_run_per_atom,
                                auto_run_per_atom_per_property,
                                auto_run_per_property)
from ichor.menu import Menu


def auto_run_per_menu():
    with Menu("Per-Value Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("a", "Per-Atom", auto_run_per_atom_menu)
        menu.add_option("p", "Per-Property", auto_run_per_atom_menu)
        menu.add_space()
        menu.add_option(
            "ap",
            "Per-Atom + Per-Property",
            auto_run_per_atom_per_property_menu,
        )


def auto_run_per_atom_menu():
    with Menu("Per-Atom Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("r", "Run per-atom", auto_run_per_atom)
        menu.add_space()
        menu.add_option("d", "Run per-atom daemon", PerAtomDaemon().start)
        menu.add_option("s", "Stop per-atom daemon", PerAtomDaemon().stop)


def auto_run_per_property_menu():
    with Menu("Per-Property Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("r", "Run per-property", auto_run_per_property)
        menu.add_space()
        menu.add_option(
            "d", "Run per-property daemon", PerPropertyDaemon().start
        )
        menu.add_option(
            "s", "Stop per-property daemon", PerPropertyDaemon().stop
        )


def auto_run_per_atom_per_property_menu():
    with Menu(
        "Per-Atom + Per-Property Menu", space=True, back=True, exit=True
    ) as menu:
        menu.add_option(
            "r", "Run per-atom + per-property", auto_run_per_atom_per_property
        )
        menu.add_space()
        menu.add_option(
            "d",
            "Run per-atom + per-property daemon",
            PerAtomPerPropertyDaemon().start,
        )
        menu.add_option(
            "s",
            "Stop per-atom + per-property daemon",
            PerAtomPerPropertyDaemon().stop,
        )
