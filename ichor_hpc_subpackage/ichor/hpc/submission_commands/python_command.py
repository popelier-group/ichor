import sys
from pathlib import Path
from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules
from ichor.hpc.submission_command import SubmissionCommand


class PythonCommand(SubmissionCommand):
    """A class which is used for any jobs that are going to run Python code

    :param python_script: A path object to the python script that is being ran
    :param args: A list of arguments (strings) which need to be passed to the python script via the command line
    """

    def __init__(self, python_script: Path, args: Optional[List[str]] = None):
        self.script = python_script
        self.args = args if args is not None else []

    @classproperty
    def modules(self) -> Modules:
        """Returns the python executable that the current ichor program is running from."""
        return ""

    @classproperty
    def command(self) -> str:
        """Returns the command(program) which is ran in the job."""
        return str(Path(sys.base_prefix) / "bin" / "python")

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job."""
        return f"{PythonCommand.command} {self.script} {' '.join(self.args)}"
