import os
import sys
from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.submission_script.python_command import PythonCommand


class ICHORCommand(PythonCommand):
    """ Class used to submit ICHOR jobs to compute nodes. Jobs are submitted using the `SubmissionScript` class.
    
    :param script: Optional path of script that needs to be executed
    :param args: Optional arguments that need to be passed to ICHOR via command line (parsed with argparse)
    """

    def __init__(
        self, script: Optional[Path] = None, args: Optional[List[str]] = None
    ):
        PythonCommand.__init__(
            self,
            script or Path(sys.argv[0]).resolve(),
            args if args is not None else [],
        )

        from ichor.arguments import Arguments
        from ichor.globals import GLOBALS

        self.args += [f"-c {Arguments.config_file}", f"-u {GLOBALS.UID}"]

    @classproperty
    def group(self) -> bool:
        return False

    def add_function_to_job(self, function_to_run: str, *args):
        """ extends self.args with the function and function arguments that need to be executed to check output"""
        arg_str = " ".join(f'"{str(arg)}"' for arg in args)
        self.args += [f"-f {function_to_run} {arg_str}"]
