from pathlib import Path
from typing import List, Optional

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.hpc.global_variables import get_param_from_config
from ichor.hpc.submission_command import SubmissionCommand


class PythonEnvironmentNotFound(Exception):
    pass


class AnacondaCommand(SubmissionCommand):
    """A class which is used for any jobs that are going to run Python code

    :param python_script: A path object to the python script that is being ran
    :param args: A list of arguments (strings) which need to be passed to the python script via the command line
    """

    def __init__(self, python_script: Path, args: Optional[List[str]] = None):
        self.script = Path(python_script)
        self.args = args if args is not None else []

    @classproperty
    def modules(self) -> list:
        """Returns the python executable that the current ichor program is running from."""
        return get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "python",
            "modules",
        )

    @property
    def data(self) -> None:
        pass

    @classproperty
    def command(self) -> str:
        """For a Python command, this loads in the virtual environment. The same python environment is going to be used
        as the one that is used for ichor."""
        # load in environment
        anaconda_env = ichor.hpc.global_variables.PLUMED_ENVIRONMENT_NAME
        ## here is where we can set plumed anaconda environment
        try:
            return f"source activate {str(anaconda_env)}"
        except:
            raise PythonEnvironmentNotFound(
                "Python environment was not found. Cannot submit Python command."
            )

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job."""
        activate_env = AnacondaCommand.command + "\n"
        anaconda_python_path = ichor.hpc.global_variables.PLUMED_PYTHON_PATH
        python_script_to_run = (
            f"{anaconda_python_path} {self.script} {' '.join(self.args)}"
        )
        return activate_env + python_script_to_run
