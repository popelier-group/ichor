import os
from typing import List, Optional

from ichor.batch_system import BATCH_SYSTEM
from ichor.common.functools import classproperty
from ichor.logging import logger
from ichor.submission_script.ichor_command import ICHORCommand
from ichor.submission_script.submision_script import SubmissionScript

class CheckManager:
    """
    Class used to check if the jobs submitted to the compute nodes via the sumbission system have ran correctly/have the correct outputs.
    Since each type of job has different outputs, each type of job

    :param check_function: A string corresponding to the name of the function to be used to check outputs of the job
    :param args_for_check_function: Arguments that need to be passed to the function that will do the checking.
    :param ntimes: How many times to retry submitting the jobs if they continue to fail.
    """

    NTRIES = "ICHOR_N_TRIES"  # bash variable name to store the number of times the command has been tried
    TASK_COMPLETED = "ICHOR_TASK_COMPLETED"  # bash variable name to store whether the commmand has completed successfully

    def __init__(
        self,
        check_function: str = "default_check",
        args_for_check_function: Optional[List[str]] = None,
        ntimes: Optional[int] = None,
    ):
        self.check_function = check_function
        self.check_args = args_for_check_function if args_for_check_function is not None else []
        self.ntimes = ntimes

    def check(self, runcmd: str) -> str:
        """ Append extra lines to the submission script file, which are used to rerun the job if it fails and check the outputs of the job
        for errors."""

        new_runcmd = ""
        if self.ntimes is not None:
            new_runcmd += f"{CheckManager.NTRIES}=0\n"
        new_runcmd += f"export {CheckManager.TASK_COMPLETED}=false\n"
        new_runcmd += f'while [ "${CheckManager.TASK_COMPLETED}" == false ]\n'
        new_runcmd += "do\n"
        new_runcmd += "\n"

        new_runcmd += runcmd

        new_runcmd += "\n"
        if self.ntimes:
            new_runcmd += f"let {CheckManager.NTRIES}++\n"
            new_runcmd += f'if [ "${CheckManager.NTRIES}" == {self.ntimes} ]\n'
            new_runcmd += "then\n"
            new_runcmd += "break\n"
            new_runcmd += "fi\n"
        python_job = ICHORCommand()
        if self.check_args:
            python_job.add_function_to_job(self.check_function, *self.check_args)
        else:
            python_job.add_function_to_job(self.check_function)
        new_runcmd += f"eval $({python_job.repr()})\n"
        new_runcmd += "done\n"
        return new_runcmd


def print_completed():
    """ Logs information about completed jobs/tasks into ICHOR log file."""
    ntasks = 0
    if SubmissionScript.DATAFILE in os.environ.keys():
        datafile = os.environ[SubmissionScript.DATAFILE]
        try:
            with open(datafile, "r") as f:
                for _ in f:
                    ntasks += 1
        # If the datafile hasn't been created then there is no tasks to complete
        except FileNotFoundError:
            pass
    task_id = 1
    if BATCH_SYSTEM.TaskID in os.environ.keys():
        task_id = int(os.environ[BATCH_SYSTEM.TaskID])
    task_last = 1
    if BATCH_SYSTEM.TaskLast in os.environ.keys():
        try:
            task_last = int(os.environ[BATCH_SYSTEM.TaskLast])
        except ValueError:
            pass  # In case SGE_TASK_LAST is undefined
    if task_last < ntasks and task_id + task_last <= ntasks:
        logger.info(f"Running Task {task_id} as {task_id + task_last}")
        task_id += task_last
        logger.info(
            f"ntasks: {ntasks} | task_id: {task_id} | task_last: {task_last}"
        )
        # prints out to standard output, which then gets evaluated with eval
        print(f"export {BATCH_SYSTEM.TaskID}={task_id}")
    else:
        # prints out to standard output, which then gets evaluated with eval
        print(f"export {CheckManager.TASK_COMPLETED}=true")


def default_check(*args, **kwargs):
    """ Default check function which always prints completed, takes in arbitrary args and kwargs to prevent
    errors when being called with arguments and keyword arguments

    Note: Although implemented, should never be used as one should implement a function that actually checks
          whether a task has completed successfully
    """
    from ichor.logging import logger
    logger.warn("Default check function being used, implement a custom function to check task has completed successfully")
    print_completed()
