"""A stand-in batch system for machines that have no queue.

ichor falls back to this when it finds neither SGE nor SLURM, which is what a laptop
or a workstation looks like, and also what a cluster looks like while its queue is
down. Submission scripts are still written, and everything that leads up to writing
them still runs, but nothing is queued: this is the dry run used to check that the
right files are produced with the right contents.

The directives at the top of the script are written with a stand-in option prefix and
stand-in environment variable names, as there is no batch system whose syntax they
could be in. The part worth checking is what goes underneath them -- the modules that
would be loaded, the datafile handling, and the command that would run.
"""

from pathlib import Path
from typing import List, Optional, Union

import ichor.hpc.global_variables

from ichor.core.common.functools import classproperty

from ichor.hpc.batch_system.batch_system import BatchSystem
from ichor.hpc.batch_system.jobs import Job, JobID
from ichor.hpc.batch_system.node import NodeType

# what a job "submitted" here is given, so that anything printing a job id has
# something to print and it is obvious nothing was really queued
DRY_RUN_JOB_ID = "dry-run"


class LocalBatchSystem(BatchSystem):
    """The batch system used when there is not one. Writes submission scripts but
    queues nothing."""

    @staticmethod
    def is_present() -> bool:
        """Always false. This is the fallback that `init_batch_system` lands on when
        no real batch system was found, rather than something detected in its own
        right."""
        return False

    @staticmethod
    def current_node() -> NodeType:
        """There are no compute nodes without a queue, so everything runs here."""
        return NodeType.LoginNode

    @classmethod
    def submit_script(
        cls,
        job_script: Path,
        hold: Optional[Union[JobID, List[JobID]]] = None,
    ) -> JobID:
        """Does not submit anything, and says so.

        The base class would run the submit command over the script. There is nothing
        to run here, and pretending by shelling out to `echo` would make a failure to
        submit look like a success in the log.

        :param job_script: The script that would have been submitted.
        :param hold: Ignored, as there is no queue for a job to wait in.
        :return: A JobID carrying a stand-in id.
        """

        ichor.hpc.global_variables.LOGGER.info(
            f"No batch system found, so {job_script} was written but not submitted. "
            "Everything up to submission ran, which is the dry run used to check "
            "what would be sent to the queue."
        )

        return JobID(job_script, cls.parse_job_id(""))

    @classmethod
    def get_queued_jobs(cls) -> List[Job]:
        """Nothing can be queued, so nothing is."""
        return []

    @classmethod
    def parse_job_id(cls, stdout: str) -> str:
        """Returns the stand-in id. A string, as SGE and SLURM both return one, so
        that anything storing or printing it is given text either way."""
        return DRY_RUN_JOB_ID

    @classmethod
    def hold_job(cls, job: Union[JobID, List[JobID]]) -> List[str]:
        """Nothing waits for anything else without a queue."""
        return []

    @classproperty
    def submit_script_command(self) -> List[str]:
        """Never used, as `submit_script` is overridden to submit nothing."""
        return []

    @classproperty
    def delete_job_command(self) -> List[str]:
        """Never used, as there is nothing queued to delete."""
        return []

    @staticmethod
    def status() -> List[str]:
        """Never used, as there is nothing queued to report on."""
        return []

    @classmethod
    def node_options(cls, include_nodes: List[str], exclude_nodes: List[str]) -> str:
        """There are no nodes to pick between."""
        return ""

    @classmethod
    def change_working_directory(cls, path: Path) -> str:
        """Returns the real path, so that the written script shows where the job
        would have run rather than a placeholder."""
        return f"-wd {path}"

    @classmethod
    def output_directory(cls, path: Path, task_array: bool = False) -> str:
        """Returns the real path, so the script shows where stdout would go."""
        return f"-o {path}"

    @classmethod
    def error_directory(cls, path: Path, task_array: bool = False) -> str:
        """Returns the real path, so the script shows where stderr would go."""
        return f"-e {path}"

    @classmethod
    def parallel_environment(cls, ncores: int) -> str:
        """Returns the core count as a directive, so that a script written here still
        records how many cores the job asked for.

        Unlike SLURM, no partition is looked up: without a queue there are no
        partitions to choose between, so a dry run is not the place to find out that
        `hpc.parallel_environments` does not cover a core count.
        """
        return f"-cores {ncores}"

    @classmethod
    def array_job(cls, njobs: int, max_running_tasks: Optional[int] = None) -> str:
        """Returns the line marking the script as an array job. These run at the same
        time in parallel as they do not depend on one another, e.g. 50 Gaussian jobs
        as one array job rather than 50 submissions."""
        array_str = f"-a 1-{njobs}"
        if max_running_tasks is not None:
            array_str += f"{min(njobs - 1, max_running_tasks)}"
        return array_str

    @classmethod
    def max_running_tasks(cls, max_running_tasks: int) -> str:
        """Returns the cap on how many tasks of an array run at once."""
        return f"-maxtasks {max_running_tasks}"

    @classproperty
    def JobID(self) -> str:
        """Stand-in name for the variable holding the job id."""
        return "ICHOR_DRY_RUN_JOB_ID"

    @classproperty
    def TaskID(self) -> str:
        """Stand-in name for the variable holding the task id, which is what indexes
        the datafile arrays in the written script."""
        return "ICHOR_DRY_RUN_TASK_ID"

    @classproperty
    def TaskLast(self) -> str:
        """Stand-in name for the variable holding the last task of an array."""
        return "ICHOR_DRY_RUN_TASK_LAST"

    @classproperty
    def Host(self) -> str:
        """Stand-in name for the variable holding the submitting host."""
        return "ICHOR_DRY_RUN_HOST"

    @classproperty
    def NumProcs(self) -> str:
        """Stand-in name for the variable holding the core count the job was given."""
        return "ICHOR_DRY_RUN_NUM_PROCS"

    @classproperty
    def OptionCmd(self) -> str:
        """Returns the prefix the directives are written with.

        Declared as a `classproperty` like the real batch systems, because it is read
        off the class rather than an instance; a plain `property` put the descriptor
        object into the script as `#<property object at 0x...>`.
        """
        return "DRY_RUN"
