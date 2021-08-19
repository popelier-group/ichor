from pathlib import Path
from typing import List, Optional

from ichor.common.functools import classproperty
from ichor.modules import Modules, PythonModules
from ichor.submission_script.command_line import CommandLine


class PythonCommand(CommandLine):
    """ A class which is used for any jobs that are going to run Python code
    
    :param python_script: A path object to the python script that is being ran
    :param args: Arguments which need to be passed to the python script via the command line (parsed with argparse)
    """

    def __init__(self, python_script: Path, args: Optional[List[str]] = None):
        self.script = python_script
        self.args = args if args is not None else []

    @classproperty
    def modules(self) -> Modules:
        """ Returns a `Modules` instance which contains modules that need to be loaded on the machine for Python to function."""
        return PythonModules

    # matt_todo: Maybe make these into class variables instead of classproperty because they are static
    @classproperty
    def command(self) -> str:
        """ Returns the command(program) which is ran in the job."""
        return "python"

    # matt_todo: variables argument not used in the function, also make self.command into PythonCommand.command instead
    def repr(self, variables=None) -> str:
        """ Returns a string which is then written into the submission script in order to run a python job."""
        return f"{self.command} {self.script} {' '.join(self.args)}"
