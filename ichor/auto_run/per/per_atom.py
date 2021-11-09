from pathlib import Path
from typing import Callable, List, Optional

from ichor.auto_run.ichor_jobs.auto_run_ichor_collate_log import \
    submit_ichor_collate_models_to_auto_run
from ichor.auto_run.per.per import auto_run_per_value
from ichor.auto_run.standard_auto_run import auto_make_models
from ichor.batch_system import JobID
from ichor.common.io import pushd
from ichor.daemon import Daemon
from ichor.file_structure import FILE_STRUCTURE
from ichor.globals import GLOBALS
from ichor.main.make_models import MODEL_TYPES, make_models
from ichor.models import Models


class PerAtomDaemon(Daemon):
    def __init__(self):
        from ichor.file_structure import FILE_STRUCTURE
        from ichor.globals import GLOBALS

        pidfile = GLOBALS.CWD / FILE_STRUCTURE["atoms_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["atoms_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["atoms_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        auto_run_per_atom()
        self.stop()


def auto_run_per_atom(run_func: Optional[Callable] = None) -> None:
    atoms = [atom.name for atom in GLOBALS.ATOMS]
    auto_run_per_value(
        "OPTIMISE_ATOM",
        atoms,
        directory=FILE_STRUCTURE["atoms"],
        run_func=run_func,
    )


def run_missing_models(atom_dir: Path, make_on_compute: bool = False) -> JobID:
    with pushd(atom_dir, update_cwd=True):
        models_found = []
        if FILE_STRUCTURE["models"].exists():
            models_found += Models(FILE_STRUCTURE["models"]).types
        models_to_make = list(set(MODEL_TYPES) - set(models_found))
        make_models_func = auto_make_models if make_on_compute else make_models
        return make_models_func(
            FILE_STRUCTURE["training_set"],
            atoms=[atom_dir.name],
            types=models_to_make,
        )


def make_missing_atom_models(make_on_compute: bool = True) -> JobID:
    job_ids = []
    for d in FILE_STRUCTURE["atoms"].iterdir():
        if d.is_dir() and d.name in GLOBALS.ATOMS.names:
            job_id = run_missing_models(
                atom_dir=d, make_on_compute=make_on_compute
            )
            job_ids.append(job_id)
    return submit_ichor_collate_models_to_auto_run(
        Path.cwd(), job_ids
    )
