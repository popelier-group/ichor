from typing import Callable, Optional

from ichor.auto_run.per.per import auto_run_per_value
from ichor.common import Daemon


class PerAtomDaemon(Daemon):
    def __init__(self):
        from ichor.globals import GLOBALS
        from ichor.file_structure import FILE_STRUCTURE

        pidfile = GLOBALS.CWD / FILE_STRUCTURE["atoms_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["atoms_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["atoms_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        auto_run_per_atom()
        self.stop()


def auto_run_per_atom(run_func: Optional[Callable] = None) -> None:
    from ichor.globals import GLOBALS
    from ichor.file_structure import FILE_STRUCTURE

    atoms = [atom.name for atom in GLOBALS.ATOMS]
    auto_run_per_value(
        "OPTIMISE_ATOM",
        atoms,
        directory=FILE_STRUCTURE["atoms"],
        run_func=run_func,
    )
