from typing import Callable, List, Optional

from ichor.auto_run.per.per import (
    auto_run_per_value,
    check_auto_run_per_counter,
)
from ichor.batch_system import JobID
from ichor.daemon import Daemon
from ichor.file_structure import FILE_STRUCTURE
from ichor.main.make_models import MODEL_TYPES


class PerPropertyDaemon(Daemon):
    def __init__(self):
        from ichor.file_structure import FILE_STRUCTURE
        from ichor.globals import GLOBALS

        pidfile = GLOBALS.CWD / FILE_STRUCTURE["properties_pid"]
        stdout = GLOBALS.CWD / FILE_STRUCTURE["properties_stdout"]
        stderr = GLOBALS.CWD / FILE_STRUCTURE["properties_stderr"]
        super().__init__(pidfile, stdout=stdout, stderr=stderr)

    def run(self):
        auto_run_per_property()
        self.stop()


def run_per_property_daemon():
    check_auto_run_per_counter(
        FILE_STRUCTURE["properties"], [ty for ty in MODEL_TYPES()]
    )
    PerPropertyDaemon().start()


def auto_run_per_property(run_func: Optional[Callable] = None) -> List[JobID]:
    properties = [ty for ty in MODEL_TYPES()]
    return auto_run_per_value(
        "OPTIMISE_PROPERTY",
        properties,
        directory=FILE_STRUCTURE["properties"],
        run_func=run_func,
    )
