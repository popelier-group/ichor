from ichor.cli.useful_functions.compile_strings_to_python_code import (
    compile_strings_to_python_code,
)
from ichor.hpc.global_variables import SCRIPT_NAMES
from ichor.hpc.submission_commands.free_flow_python_command import FreeFlowPythonCommand
from ichor.hpc.submission_script import SubmissionScript


def submit_free_flow_python_command_on_compute(text_list, script_name, ncores):

    final_cmd = compile_strings_to_python_code(text_list)
    py_cmd = FreeFlowPythonCommand(final_cmd)
    with SubmissionScript(
        SCRIPT_NAMES[script_name], ncores=ncores
    ) as submission_script:

        submission_script.add_command(py_cmd)

    submission_script.submit()
