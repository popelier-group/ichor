from pathlib import Path
from typing import List, Optional, Union

from ichor.core.common.types.itypes import F
from ichor.hpc.submission_script.python_command import PythonCommand


class ICHORCommand(PythonCommand):
    """Class used to submit ICHOR jobs to compute nodes. Jobs are submitted using the `SubmissionScript` class.

    :param script: Optional path of script that needs to be executed
    :param args: Optional arguments that need to be passed to ICHOR via command line (parsed with argparse)
    """

    def __init__(
        self,
        script: Optional[Path] = None,
        args: Optional[List[str]] = None,
        func: Optional[Union[str, F]] = None,
        func_args: Optional[List[str]] = None,
    ):
        super().__init__(script, args)

        if func is not None:
            func_args = func_args if func_args else []
            self.add_function_to_job(func, *func_args)

    def add_function_to_job(self, function_to_run: Union[str, F], *args):
        """extends self.args with the function and function arguments that need to be executed to check output"""

        if not isinstance(function_to_run, str):
            function_to_run = function_to_run.__name__
        arg_str = " ".join(f'"{arg}"' for arg in args)
        self.args += [f"-f {function_to_run} {arg_str}"]
