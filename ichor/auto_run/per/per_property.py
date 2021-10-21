from typing import Callable, Optional

from ichor.auto_run.per.per import auto_run_per_value
from ichor.daemon import Daemon


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


def auto_run_per_property(run_func: Optional[Callable] = None) -> None:
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.main.make_models import ModelType

    properties = [ty.value for ty in ModelType]
    auto_run_per_value(
        "OPTIMISE_PROPERTY",
        properties,
        directory=FILE_STRUCTURE["properties"],
        run_func=run_func,
    )
