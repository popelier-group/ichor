import os
import sys
from pathlib import Path
from typing import List, Optional, Union

import ichor
from ichor.ichor_lib.common.functools import classproperty
from ichor.ichor_lib.itypes import F
from ichor.programs import get_ichor_parent_directory
from ichor.submission_script.python_command import PythonCommand


class ICHORCommand(PythonCommand):
    """Class used to submit ICHOR jobs to compute nodes. Jobs are submitted using the `SubmissionScript` class.

    :param script: Optional path of script that needs to be executed
    :param args: Optional arguments that need to be passed to ICHOR via command line (parsed with argparse)
    """

    def __init__(
        self,
        script: Optional[Path] = None,
        args: Optional[List[str]] = None,
        auto_run: bool = False,
        func: Optional[Union[str, F]] = None,
        func_args: Optional[List[str]] = None,
        needs_uid: Optional[bool] = True,
    ):
        PythonCommand.__init__(
            self,
            script or get_ichor_parent_directory(),
            args if args is not None else [],
        )

        from ichor.ichor_hpc.arguments import Arguments
        from ichor.ichor_hpc import GLOBALS

        self.needs_uid = needs_uid

        self.args += [f"-c {Arguments.config_file}"]

        if self.needs_uid:
            self.args += [f"-u {GLOBALS.UID}"]

        if auto_run:
            self.args += ["-ar"]

        if func is not None:
            func_args = func_args if func_args is not None else []
            self.add_function_to_job(func, *func_args)

    @classproperty
    def group(self) -> bool:
        return False

    def add_function_to_job(self, function_to_run: Union[str, F], *args):
        """extends self.args with the function and function arguments that need to be executed to check output"""
        if not isinstance(function_to_run, str):
            function_to_run = function_to_run.__name__
        arg_str = " ".join(f'"{arg}"' for arg in args)
        self.args += [f"-f {function_to_run} {arg_str}"]
