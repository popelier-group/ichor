from pathlib import Path
from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules, PythonModules
from ichor.hpc.submission_script.command_line import CommandLine


class PythonCommand(CommandLine):
    """A class which is used for any jobs that are going to run Python code

    :param python_script: A path object to the python script that is being ran
    :param args: Arguments which need to be passed to the python script via the command line (parsed with argparse)
    """

    def __init__(self, python_script: Path, args: Optional[List[str]] = None):
        self.script = python_script
        self.args = args if args is not None else []

    @classproperty
    def modules(self) -> Modules:
        """Returns a `Modules` instance which contains modules that need to be loaded on the machine for Python to function."""
        return PythonModules

    @classproperty
    def command(self) -> str:
        """Returns the command(program) which is ran in the job."""
        return "python3"

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job."""
        return f"{PythonCommand.command} {self.script} {' '.join(self.args)}"
