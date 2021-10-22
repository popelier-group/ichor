from ichor.auto_run.per import (PerAtomDaemon, PerAtomPerPropertyDaemon,
                                PerPropertyDaemon, auto_run_per_atom,
                                auto_run_per_atom_per_property,
                                auto_run_per_property,
                                delete_child_process_jobs,
                                find_child_processes_recursively,
                                make_missing_atom_models,
                                ReRunDaemon,
                                stop_all_child_processes)
from ichor.menu import Menu
from ichor.tab_completer import ListCompleter

child_processes = []
all_child_processes = []

child_processes_selected = False


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
        menu.add_space()
        menu.add_option(
            "c", "Control Child Processes", control_child_processes_menu
        )


def auto_run_per_atom_menu():
    with Menu("Per-Atom Menu", space=True, back=True, exit=True) as menu:
        menu.add_option("r", "Run per-atom", auto_run_per_atom)
        menu.add_space()
        menu.add_option("d", "Run per-atom daemon", PerAtomDaemon().start)
        menu.add_option("s", "Stop per-atom daemon", PerAtomDaemon().stop)
        menu.add_space()
        menu.add_option(
            "m", "Make model for all properties", make_missing_atom_models
        )


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


def edit_list_of_child_processes():
    # todo: make this a general purpose routine, it is a repeat of main/make_models.py
    global child_processes
    global child_processes_selected
    if not child_processes_selected:
        child_processes = []
    while True:
        Menu.clear_screen()
        print("Select Child Processes")
        child_process_options = [
            str(i + 1) for i in range(len(all_child_processes))
        ] + ["all", "c", "clear"]
        with ListCompleter(child_process_options):
            for i, cp in enumerate(all_child_processes):
                print(
                    f"[{i+1}] [{'x' if cp in child_processes else ' '}] {cp}"
                )
            print()
            ans = input(">> ")
            ans = ans.strip().lower()
            if ans == "":
                break
            elif ans in child_process_options:
                idx = int(ans) - 1
                if all_child_processes[idx] in child_processes:
                    del child_processes[
                        child_processes.index(all_child_processes[idx])
                    ]
                else:
                    child_processes += [all_child_processes[idx]]
            elif ans in ["all"]:
                child_processes = list(all_child_processes)
            elif ans in ["c", "clear"]:
                child_processes.clear()
            else:
                print("Invalid Input")
    child_processes_selected = True


def add_child_processes_to_menu(menu: Menu) -> Menu:
    menu.add_message("Child Processes:")
    for child_process in child_processes:
        menu.add_message(f"- {child_process}")
    return menu


def child_process_queue_menu() -> None:
    with Menu(
        "Child Process Queue Menu", space=True, back=True, exit=True
    ) as menu:
        menu = add_child_processes_to_menu(menu)
        menu.add_space()
        menu.add_option(
            "del",
            "Delete all jobs running for each child process",
            delete_child_process_jobs,
            kwargs={"child_processes": child_processes},
        )


def control_child_processes_menu_refresh(menu: Menu) -> None:
    global child_processes
    menu.clear_options()

    menu = add_child_processes_to_menu(menu)
    menu.add_space()
    menu.add_option(
        "e", "Edit Child Process List", edit_list_of_child_processes
    )
    menu.add_space()
    menu.add_option(
        "rerun", "Rerun failed auto-runs", ReRunDaemon().start()
    )
    menu.add_option(
        "stop", "Stop all child processes", stop_all_child_processes
    )
    menu.add_option(
        "q", "Queue Options For Child Processes", child_process_queue_menu
    )

    menu.add_final_options()


def control_child_processes_menu() -> None:
    global child_processes
    global all_child_processes
    child_processes = find_child_processes_recursively()
    all_child_processes = list(child_processes)
    with Menu(
        "Child Processes Menu", refresh=control_child_processes_menu_refresh
    ):
        pass
