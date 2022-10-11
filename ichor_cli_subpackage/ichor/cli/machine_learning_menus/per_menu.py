from pathlib import Path
from typing import List

from ichor.core.menu import Menu, MenuVar, select_multiple_from_list
from ichor.hpc.auto_run.per import (PerAtomDaemon, PerAtomPerPropertyDaemon,
                                    PerPropertyDaemon, ReRunDaemon,
                                    auto_run_per_atom,
                                    auto_run_per_atom_per_property,
                                    auto_run_per_property,
                                    delete_child_process_jobs,
                                    find_child_processes_recursively,
                                    make_models_atoms_menu,
                                    run_per_atom_daemon,
                                    run_per_atom_per_property_daemon,
                                    run_per_property_daemon,
                                    stop_all_child_processes)
from ichor.hpc.auto_run.per.child_processes import (
    concat_dir_to_ts, print_child_processes_status)
from maybe_not_needed.collate_log import collate_model_log


def auto_run_per_menu():
    with Menu("Per-Value Menu") as menu:
        menu.add_option("a", "Per-Atom", auto_run_per_atom_menu)
        menu.add_option("p", "Per-Property", auto_run_per_property)
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
    with Menu("Per-Atom Menu") as menu:
        menu.add_option("r", "Run per-atom", auto_run_per_atom)
        menu.add_space()
        menu.add_option("d", "Run per-atom daemon", run_per_atom_daemon)
        menu.add_option("s", "Stop per-atom daemon", PerAtomDaemon().stop)
        menu.add_space()
        menu.add_option(
            "m", "Make model for all properties", make_models_atoms_menu
        )


def auto_run_per_property_menu():
    with Menu("Per-Property Menu") as menu:
        menu.add_option("r", "Run per-property", auto_run_per_property)
        menu.add_space()
        menu.add_option(
            "d", "Run per-property daemon", run_per_property_daemon
        )
        menu.add_option(
            "s", "Stop per-property daemon", PerPropertyDaemon().stop
        )


def auto_run_per_atom_per_property_menu():
    with Menu("Per-Atom + Per-Property Menu") as menu:
        menu.add_option(
            "r", "Run per-atom + per-property", auto_run_per_atom_per_property
        )
        menu.add_space()
        menu.add_option(
            "d",
            "Run per-atom + per-property daemon",
            run_per_atom_per_property_daemon,
        )
        menu.add_option(
            "s",
            "Stop per-atom + per-property daemon",
            PerAtomPerPropertyDaemon().stop,
        )


def child_process_queue_menu(child_processes: MenuVar[List[Path]]) -> None:
    with Menu("Child Process Queue Menu") as menu:
        menu.add_var(child_processes)
        menu.add_space()
        menu.add_option(
            "del",
            "Delete all jobs running for each child process",
            delete_child_process_jobs,
            kwargs={"child_processes": child_processes},
        )


def child_processes_formatter(child_processes: List[Path]) -> str:
    result = "\n\n"
    for child_process in child_processes:
        result += f"- {child_process}\n"
    result += "\n"
    return result


def control_child_processes_menu() -> None:
    all_child_processes = find_child_processes_recursively()
    child_processes = MenuVar(
        "Child Processes",
        list(all_child_processes),
        custom_formatter=child_processes_formatter,
    )
    with Menu("Child Processes Menu") as menu:
        menu.add_var(child_processes)
        menu.add_space()
        menu.add_option(
            "e",
            "Edit Child Process List",
            select_multiple_from_list,
            args=[
                all_child_processes,
                child_processes,
                "Select Child Processes",
            ],
        )
        menu.add_space()
        menu.add_option(
            "log",
            "Collate Model Logs from Child Processes",
            collate_model_log,
            kwargs={"child_processes": child_processes},
        )
        menu.add_option(
            "rerun", "Rerun failed auto-runs", ReRunDaemon().start
        )  # todo: this probably needs child processes as an argument?
        menu.add_option(
            "stat",
            "Get Status of Child Processes",
            print_child_processes_status,
            kwargs={"child_processes": child_processes},
            wait=True,
        )
        menu.add_option(
            "stop",
            "Stop child processes",
            stop_all_child_processes,
            kwargs={"child_processes": child_processes},
        )
        menu.add_space()
        menu.add_option(
            "concat",
            "Concatenate PointsDirectory to Child Processes Training Set",
            concat_dir_to_ts,
            kwargs={"child_processes": child_processes},
        )
