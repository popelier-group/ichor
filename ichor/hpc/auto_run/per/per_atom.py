from pathlib import Path
from typing import Callable, List, Optional

from ichor.cli.menus.machine_learning_menus import make_models
from ichor.cli.menus.menu import Menu  # todo: fix this
from ichor.cli.menus.tab_completer import ListCompleter  # todo: fix this
from ichor.core.common.io import pushd
from ichor.hpc.auto_run.ichor_jobs.auto_run_ichor_collate_log import (
    submit_ichor_collate_models_to_auto_run,
)
from ichor.hpc.auto_run.per.per import (
    auto_run_per_value,
    check_auto_run_per_counter,
)
from ichor.hpc.auto_run.standard_auto_run import auto_make_models
from ichor.hpc.batch_system import JobID
from ichor.hpc.daemon import Daemon
from ichor.hpc.programs.qct import (
    QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
    QuantumChemicalTopologyProgram,
)

_atoms_to_run_on: Optional[List[Path]] = None
_selected_atoms_to_run_on: Optional[List[Path]] = None


class PerAtomDaemon(Daemon):
    def __init__(self):
        from ichor.hpc import FILE_STRUCTURE, GLOBALS

        pidfile = GLOBALS.CWD / FILE_STRUCTURE["atoms_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["atoms_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["atoms_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        auto_run_per_atom()
        self.stop()


def run_per_atom_daemon():
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

    check_auto_run_per_counter(
        FILE_STRUCTURE["atoms"], [atom.name for atom in GLOBALS.ATOMS]
    )
    PerAtomDaemon().start()


def auto_run_per_atom(run_func: Optional[Callable] = None) -> List[JobID]:
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

    atoms = [atom.name for atom in GLOBALS.ATOMS]
    return auto_run_per_value(
        "OPTIMISE_ATOM",
        atoms,
        directory=FILE_STRUCTURE["atoms"],
        run_func=run_func,
    )


def run_missing_models(atom_dir: Path, make_on_compute: bool = False) -> JobID:
    with pushd(atom_dir, update_cwd=True):
        from ichor.hpc import FILE_STRUCTURE

        make_models_func = (
            auto_make_models if make_on_compute else make_models.make_models
        )
        return make_models_func(
            FILE_STRUCTURE["training_set"],
            atoms=[atom_dir.name],
            types=make_models.model_types,
        )


def make_missing_atom_models(
    atoms: Optional[List[Path]] = None, make_on_compute: bool = True
) -> JobID:
    if atoms is None:
        if _selected_atoms_to_run_on is None:
            _setup_atoms_to_run_on()
            _setup_model_types()
        atoms = list(_selected_atoms_to_run_on)
    job_ids = [
        run_missing_models(atom, make_on_compute=make_on_compute)
        for atom in atoms
    ]
    return submit_ichor_collate_models_to_auto_run(Path.cwd(), job_ids)


def make_models_menu_refresh(menu):
    from ichor.hpc import GLOBALS

    """
    This is a `refresh` function that takes in an instance of a menu and add options to it. See `class Menu` `refresh` attrubute.
    By defining a custom refresh function, when the menu refreshes we can clear the menu options to refresh the messages so they
    update when changed by the user

    :param menu: An instance of `class Menu` to which options are added.
    """
    menu.clear_options()
    menu.add_option(
        "1",
        "Make Models",
        make_missing_atom_models,
        kwargs={"atoms": _selected_atoms_to_run_on},
    )
    menu.add_space()
    menu.add_option("t", "Select Model Type", make_models.select_model_type)
    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        menu.add_option(
            "d",
            "Toggle Add Dispersion to IQA",
            make_models.toggle_add_dispersion,
        )
    menu.add_option("a", "Select Atoms", _select_atoms_to_run_on)
    menu.add_space()
    menu.add_message(f"Model Type(s): {', '.join(make_models.model_types)}")
    if (
        QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
        is QuantumChemicalTopologyProgram.Morfi
    ):
        menu.add_message(
            f"Add Dispersion to IQA: {GLOBALS.ADD_DISPERSION_TO_IQA}"
        )
    menu.add_message("Atoms:")
    if _atoms_to_run_on is None:
        _setup_atoms_to_run_on()
    for atom in _selected_atoms_to_run_on:
        menu.add_message(f"- {atom}")
    menu.add_final_options()


def _select_atoms_to_run_on():
    # todo: make this a general purpose routine, it is a repeat of main/make_models.py
    global _selected_atoms_to_run_on
    while True:
        Menu.clear_screen()
        print("Select Child Processes")
        atoms_options = [str(i + 1) for i in range(len(_atoms_to_run_on))] + [
            "all",
            "c",
            "clear",
        ]
        with ListCompleter(atoms_options):
            for i, cp in enumerate(_atoms_to_run_on):
                print(
                    f"[{i+1}] [{'x' if cp in _selected_atoms_to_run_on else ' '}] {cp}"
                )
            print()
            ans = input(">> ")
            ans = ans.strip().lower()
            if ans == "":
                break
            elif ans in atoms_options:
                idx = int(ans) - 1
                if _atoms_to_run_on[idx] in _selected_atoms_to_run_on:
                    del _selected_atoms_to_run_on[
                        _selected_atoms_to_run_on.index(_atoms_to_run_on[idx])
                    ]
                else:
                    _selected_atoms_to_run_on += [_atoms_to_run_on[idx]]
            elif ans in ["all"]:
                _selected_atoms_to_run_on = list(_atoms_to_run_on)
            elif ans in ["c", "clear"]:
                _selected_atoms_to_run_on.clear()
            else:
                print("Invalid Input")


def _setup_atoms_to_run_on():
    from ichor.hpc import FILE_STRUCTURE, GLOBALS

    global _selected_atoms_to_run_on
    global _atoms_to_run_on
    _atoms_to_run_on = [
        d
        for d in FILE_STRUCTURE["atoms"].iterdir()
        if d.is_dir() and d.name in GLOBALS.ATOMS.names
    ]
    _selected_atoms_to_run_on = list(_atoms_to_run_on)


def _setup_model_types():
    make_models.model_types = make_models.MODEL_TYPES()


# todo: move this to cli
def make_models_atoms_menu():
    """The handler function for making models from a specific directory. To make the models, both Gaussian and AIMALL have to be ran
    for the points that are in the directory."""
    # use context manager here because we need to run the __enter__ and __exit__ methods.
    # Make an instance called `menu` and set its `self.refresh` to `make_models_menu_refresh`, which gets called in the menu's `run` method
    _setup_atoms_to_run_on()
    _setup_model_types()
    with Menu("Make Models Menu", refresh=make_models_menu_refresh) as menu:
        pass
