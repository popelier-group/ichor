from typing import List

from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript


def compile_strings_to_python_code(strings_list: List[str]) -> str:
    """Takes in a list of strings and concats them with a ; character
    Then these strings can be executed with python -c

    :param strings_list: _description_
    :type strings_list: List[str]
    :return: _description_
    :rtype: str
    """

    return ";".join(strings_list)


def submit_free_flow_python_command_on_compute(text_list, script_name, ncores):

    final_cmd = compile_strings_to_python_code(text_list)
    py_cmd = FreeFlowPythonCommand(final_cmd)
    with SubmissionScript(
        SCRIPT_NAMES[script_name], ncores=ncores
    ) as submission_script:

        submission_script.add_command(py_cmd)

    return submission_script.submit()
