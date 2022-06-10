from typing import Callable, List, Optional

from ichor.cli.menus.machine_learning_menus.make_models import MODEL_TYPES
from ichor.core.daemon import Daemon
from ichor.hpc import FILE_STRUCTURE
from ichor.hpc.auto_run.per.per import (
    auto_run_per_value,
    check_auto_run_per_counter,
)
from ichor.hpc.batch_system import JobID


class PerPropertyDaemon(Daemon):
    def __init__(self):
        from ichor.hpc import FILE_STRUCTURE, GLOBALS

        pidfile = GLOBALS.CWD / FILE_STRUCTURE["properties_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["properties_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["properties_stderr"]
        super().__init__(
            pidfile,
            stdout=stdout,
            stderr=stderr,
            pid_store=FILE_STRUCTURE["pids"],
        )

    def run(self):
        auto_run_per_property()
        self.stop()


def run_per_property_daemon():
    check_auto_run_per_counter(
        FILE_STRUCTURE["properties"], list(MODEL_TYPES())
    )
    PerPropertyDaemon().start()


def auto_run_per_property(run_func: Optional[Callable] = None) -> List[JobID]:
    properties = list(MODEL_TYPES())
    return auto_run_per_value(
        "OPTIMISE_PROPERTY",
        properties,
        directory=FILE_STRUCTURE["properties"],
        run_func=run_func,
    )
