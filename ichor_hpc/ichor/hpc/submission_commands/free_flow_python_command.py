from typing import List, Optional

from ichor.hpc.submission_commands.python_command import PythonCommand


class FreeFlowPythonCommand(PythonCommand):
    """A class which is used for jobs that will execute python code
    with python -c `python_code_here`

    :param text: Arbitrary text to get compiled with python and get executed on a compute node.
    """

    def __init__(self, text: str):
        self.text = text

    def repr(self, variables: Optional[List[str]] = None) -> str:
        """Returns a string which is then written into the submission script in order to run a python job."""
        activate_env = PythonCommand.command + "\n"
        python_script_to_run = f'python3 -c "{self.text}"'
        return activate_env + python_script_to_run
