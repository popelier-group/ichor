from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty
from ichor.core.common.os import run_cmd

from ichor.hpc.batch_system.jobs import Job, JobID
from ichor.hpc.batch_system.node import NodeType


class BatchSystem(ABC):
    """An abstract base class for batch systems which are the systems used
    to submit jobs to compute nodes (for example Sun Grid Engine.)"""

    @staticmethod
    @abstractmethod
    def is_present() -> bool:
        pass

    @staticmethod
    @abstractmethod
    def current_node() -> NodeType:
        """Return the type of the node ichor is currently running on e.g. NodeType.ComputeNode"""
        pass

    @classmethod
    def submit_script(
        cls,
        job_script: Path,
        hold: Optional[Union[JobID, List[JobID]]] = None,
    ) -> JobID:
        """Submit a job script to the batch system in order to queue/run jobs."""
        cmd = cls.submit_script_command
        if hold:
            cmd += cls.hold_job(hold)
        cmd += [job_script]

        ichor.hpc.global_variables.LOGGER.debug(
            f"Submitting Script Using Command: {' '.join(map(str, cmd))}"
        )

        stdout, stderr = run_cmd(
            cmd
        )  # this is the part which actually submits the job to  the queuing system
        ichor.hpc.global_variables.LOGGER.debug(
            f"- stdout: '{stdout}' | stderr: '{stderr}'"
        )
        job_id = JobID(
            job_script, cls.parse_job_id(stdout)
        )  # stdout is parsed because this is where the job id is printed once a job is submitted
        ichor.hpc.global_variables.LOGGER.debug(f"- job_id: {job_id}")
        return job_id

    @classmethod
    @abstractmethod
    def get_queued_jobs(cls) -> List[Job]:
        pass

    @classmethod
    def delete(cls, job: JobID):
        """Delete submitted jobs on the batch system."""
        cmd = cls.delete_job_command + [job.id]
        stdout, stderr = run_cmd(cmd)

    @classmethod
    @abstractmethod
    def parse_job_id(cls, stdout: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def hold_job(cls, job: Union[JobID, List[JobID]]):
        """Hold a job in order for it to be ran at another time/ after another job has finished running."""
        pass

    @classproperty
    @abstractmethod
    def submit_script_command(self) -> List[str]:
        """Command to submit job to compute node, such as `qsub`."""
        pass

    @classmethod
    def delete_job(cls, job_id: JobID) -> str:
        """Delete job submitted to compute node."""
        cmd = [cls.delete_job_command, job_id]
        stdout, _ = run_cmd(cmd)
        return stdout

    @classmethod
    @abstractmethod
    def node_options(cls, include_nodes: List[str], exclude_nodes: List[str]) -> str:
        pass

    @classproperty
    @abstractmethod
    def delete_job_command(self) -> List[str]:
        """Command that is used to delete a job, such as `qdel`."""
        pass

    @staticmethod
    @abstractmethod
    def status() -> str:
        """Returns the status of running jobs."""
        pass

    @classmethod
    @abstractmethod
    def change_working_directory(cls, path: Path) -> str:
        """ " Changes the working directory"""
        pass

    @classmethod
    @abstractmethod
    def output_directory(cls, path: Path, task_array: bool = False) -> str:
        """Changes the output directory where (these are .o files)"""
        pass

    @classmethod
    @abstractmethod
    def error_directory(cls, path: Path, task_array: bool = False) -> str:
        """Changes the error directory where (these are .e files)"""
        pass

    @classmethod
    @abstractmethod
    def parallel_environment(cls, ncores: int) -> Optional[str]:
        """Returns the flag to set the parallel environment for the job"""
        pass

    @classmethod
    @abstractmethod
    def array_job(cls, njobs: int) -> str:
        """Returns the flag to set the number of tasks for a job"""
        pass

    @classmethod
    @abstractmethod
    def max_running_tasks(cls, max_running_tasks: int) -> str:
        """Returns the flag to se the maximum number of running tasks for a job"""
        pass

    @classproperty
    @abstractmethod
    def JobID(self) -> str:
        """Returns environment variable name to get the current job id, not currently used"""
        pass

    @classproperty
    @abstractmethod
    def TaskID(self) -> str:
        """Returns environment variable name for the current task id,
        used to index datafile arrays and by CheckManager"""
        pass

    @classproperty
    @abstractmethod
    def TaskLast(self) -> str:
        """Returns environment variable name for the last task in a task array, used by CheckManager"""
        pass

    @classproperty
    @abstractmethod
    def Host(self) -> str:
        """Returns environment variable name for the batch system host"""
        pass

    @classproperty
    @abstractmethod
    def NumProcs(self) -> str:
        """Returns environment variable name for the number of processors
        assigned to a job, used to set OpenMP etc."""
        pass

    @classproperty
    @abstractmethod
    def OptionCmd(self) -> str:
        """Returns the character used to define a batch system option statement in a submission script"""
        pass
