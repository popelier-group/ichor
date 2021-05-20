from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.modules import Modules, PythonModules
from ichor.submission_script.python import PythonCommand


class ICHORCommand(PythonCommand):
    def __init__(
        self, script: Optional[Path] = None, args: Optional[List[str]] = None
    ):
        PythonCommand.__init__(
            self,
            script or Path(__file__).resolve(),
            args if args is not None else [],
        )

        from ichor.arguments import Arguments

        self.args += [f"-c {Arguments.config_file}", f"-u {Arguments.uid}"]

    def run_function(self, function_to_run, *args):
        self.args += [f"-f {function_to_run} {' '.join(args)}"]
