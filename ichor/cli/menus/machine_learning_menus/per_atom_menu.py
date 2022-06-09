from pathlib import Path
from typing import Callable, List, Optional

from ichor.cli.menus.machine_learning_menus.make_models import (
    MODEL_TYPES,
    make_models,
)
from ichor.core.common.io import pushd
from ichor.core.menu import (
    ListCompleter,
    Menu,
    MenuVar,
    select_multiple_from_list,
    toggle_bool_var,
)
from ichor.hpc import FILE_STRUCTURE, GLOBALS
from ichor.hpc.auto_run.ichor_jobs.auto_run_ichor_collate_log import (
    submit_ichor_collate_models_to_auto_run,
)
from ichor.hpc.auto_run.per.per import (
    auto_run_per_value,
    check_auto_run_per_counter,
)
from ichor.hpc.auto_run.standard_auto_run import auto_make_models
from ichor.hpc.batch_system import JobID
from ichor.hpc.daemon.daemon import Daemon
from ichor.hpc.programs.qct import (
    QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
    QuantumChemicalTopologyProgram,
)


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
    check_auto_run_per_counter(
        FILE_STRUCTURE["atoms"], [atom.name for atom in GLOBALS.ATOMS]
    )
    PerAtomDaemon().start()


def auto_run_per_atom(run_func: Optional[Callable] = None) -> List[JobID]:
    atoms = [atom.name for atom in GLOBALS.ATOMS]
    return auto_run_per_value(
        "OPTIMISE_ATOM",
        atoms,
        directory=FILE_STRUCTURE["atoms"],
        run_func=run_func,
    )


def run_missing_models(
    atom_dir: Path, model_types: List[str], make_on_compute: bool = False
) -> JobID:
    from ichor.cli.menus.machine_learning_menus.make_models import (
        make_models as mm_func,
    )

    with pushd(atom_dir, update_cwd=True):
        make_models_func = auto_make_models if make_on_compute else mm_func
        return make_models_func(
            FILE_STRUCTURE["training_set"],
            atoms=[atom_dir.name],
            types=model_types,
        )


def make_missing_atom_models(
    atoms: List[Path], model_types: List[str], make_on_compute: bool = True
) -> JobID:
    job_ids = [
        run_missing_models(atom, model_types, make_on_compute=make_on_compute)
        for atom in atoms
    ]
    return submit_ichor_collate_models_to_auto_run(Path.cwd(), job_ids)


def make_models_atoms_menu():
    """The handler function for making models from a specific directory. To make the models, both Gaussian and AIMALL have to be ran
    for the points that are in the directory."""
    # use context manager here because we need to run the __enter__ and __exit__ methods.
    # Make an instance called `menu` and set its `self.refresh` to `make_models_menu_refresh`, which gets called in the menu's `run` method

    all_atoms = [
        d
        for d in FILE_STRUCTURE["atoms"].iterdir()
        if d.is_dir() and d.name in GLOBALS.ATOMS.names
    ]
    selected_atoms = MenuVar("Atoms", list(all_atoms))

    model_types = MenuVar("Model Types", MODEL_TYPES())

    add_dispersion_to_iqa = MenuVar("Add Dispersion to IQA", False)

    with Menu("Make Models Menu") as menu:
        menu.add_option(
            "1",
            "Make Models",
            make_missing_atom_models,
            args=[selected_atoms, model_types],
        )
        menu.add_space()
        menu.add_option(
            "t",
            "Select Model Type",
            select_multiple_from_list,
            args=[MODEL_TYPES(), model_types, "Select Model Types"],
        )
        if (
            QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
            is QuantumChemicalTopologyProgram.Morfi
        ):
            menu.add_option(
                "d",
                "Toggle Add Dispersion to IQA",
                toggle_bool_var,
                args=[add_dispersion_to_iqa],
            )
        menu.add_option(
            "a",
            "Select Atoms",
            select_multiple_from_list,
            args=[all_atoms, selected_atoms, "Select Atoms"],
        )
        menu.add_space()
        menu.add_var(model_types)
        if (
            QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
            is QuantumChemicalTopologyProgram.Morfi
        ):
            menu.add_var(add_dispersion_to_iqa)
        menu.add_var(selected_atoms)
        menu.add_message("Atoms:")
