from typing import List, Optional

from ichor.core.common.functools import classproperty
from ichor.hpc.batch_system.node import NodeType


class LocalBatchSystem:
    """LocalBatchSystem is to only be used for debugging purposes
    (Unless one wants to implement a batch system to run on a local machine... would be a nice addition)"""

    @staticmethod
    def current_node() -> NodeType:
        return NodeType.LoginNode

    @classproperty
    def delete_job_command(self) -> List[str]:
        return ["echo"]

    @staticmethod
    def status() -> List[str]:
        return ["echo"]

    @classproperty
    def submit_script_command(self) -> List[str]:
        return ["echo"]

    @classmethod
    def parse_job_id(cls, stdout) -> List[str]:
        return ["test1234"]

    @classmethod
    def change_working_directory(cls, dir):
        return "."

    @classmethod
    def output_directory(cls, d, task_array=False):
        return "."

    @classmethod
    def error_directory(cls, d, task_array=False):
        return "."

    @classmethod
    def parallel_environment(cls, cores):
        return 2

    @property
    def OptionCmd(self) -> str:
        return "test"

    @classmethod
    def array_job(cls, njobs: int, max_running_tasks: Optional[int] = None) -> str:
        """Returns the line in the job script that specifies this job is an array job.
        These jobs are run at the same time in parallel
        as they do not depend on one another. An example will be running 50 Gaussian
        or AIMALL jobs at the same time without having to submit
        50 separate jobs. Instead 1 array job can be submitted."""
        array_str = f"-a 1-{njobs}"
        if max_running_tasks is not None:
            array_str += f"{min(njobs-1, max_running_tasks)}"
        return array_str
