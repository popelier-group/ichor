from pathlib import Path
from typing import List, Optional

from ichor.hpc.batch_system import JobID
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


def submit_free_flow_python_command_on_compute(
    text_list,
    script_name,
    ncores,
    hold: Optional[JobID] = None,
    outputs_dir_path: Optional[Path] = None,
    errors_dir_path: Optional[Path] = None,
):
    """Writes out and submits a submission script which runs the given python code
    with `python -c` on a compute node.

    :param text_list: A list of strings, each of which is a line of python code
    :param script_name: Path to write the submission script out to
    :param ncores: Number of cores to run the job with
    :param hold: An optional JobID to hold for. The python job will not run until
        that other job has finished, defaults to None
    :param outputs_dir_path: Optional path to the directory where stdout is written
    :param errors_dir_path: Optional path to the directory where stderr is written
    """

    final_cmd = compile_strings_to_python_code(text_list)
    py_cmd = FreeFlowPythonCommand(final_cmd)
    with SubmissionScript(
        script_name,
        ncores=ncores,
        outputs_dir_path=outputs_dir_path,
        errors_dir_path=errors_dir_path,
    ) as submission_script:

        submission_script.add_command(py_cmd)

    return submission_script.submit(hold=hold)
