from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.hpc.modules import Modules
from ichor.hpc.submission_command import SubmissionCommand


class PythonEnvironmentNotFound(Exception):
    pass


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

    @property
    def data(self) -> None:
        pass

    @classproperty
    def command(self) -> str:
        """For a Python command, this loads in the virtual environment"""
        # load in environment
        python_env = ichor.hpc.global_variables.CURRENT_PYTHON_ENVIRONMENT_PATH
        if python_env.uses_venv:
            env_path = python_env.venv_path.absolute()
            activate_script = env_path / "bin" / "activate"
            return f"source {str(activate_script)}"
        elif python_env.uses_conda:
            env_path = python_env.conda_path.absolute()
            return f"conda activate {str(env_path)}"

        raise PythonEnvironmentNotFound(
            "Python environment was not found. Cannot submit Python command."
        )

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job."""
        activate_env = PythonCommand.command + "\n"
        python_script_to_run = f"python3 {self.script} {' '.join(self.args)}"
        return activate_env + python_script_to_run
