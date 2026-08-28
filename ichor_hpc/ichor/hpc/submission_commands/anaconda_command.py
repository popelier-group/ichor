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
        """Returns the line which activates the conda environment that the job runs
        in, which is the one named by `software.python.env_name` in the ichor config
        file rather than the environment ichor itself is running from.

        :raises PythonEnvironmentNotFound: If the config file does not name an
            environment for this machine, as an unset value would otherwise be
            written into the submission script as the literal text `None` and the
            job would fail on the compute node.
        """
        # load in environment
        anaconda_env = get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "python",
            "env_name",
        )

        if not anaconda_env:
            raise PythonEnvironmentNotFound(
                "software.python.env_name is not set for this machine in "
                f"{ichor.hpc.global_variables.CONFIG_DESCRIPTION}, so there is no "
                "conda environment to activate. Cannot submit Python command."
            )

        return f"source activate {anaconda_env}"

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job.

        :raises PythonEnvironmentNotFound: If the config file does not name an
            environment or an interpreter for this machine.
        """
        activate_env = AnacondaCommand.command + "\n"
        anaconda_python_path = get_param_from_config(
            ichor.hpc.global_variables.ICHOR_CONFIG,
            ichor.hpc.global_variables.MACHINE,
            "software",
            "python",
            "python_path",
        )

        if not anaconda_python_path:
            raise PythonEnvironmentNotFound(
                "software.python.python_path is not set for this machine in "
                f"{ichor.hpc.global_variables.CONFIG_DESCRIPTION}, so there is no "
                "interpreter to run the script with. Cannot submit Python command."
            )

        python_script_to_run = (
            f"{anaconda_python_path} {self.script} {' '.join(self.args)}"
        )
        return activate_env + python_script_to_run
