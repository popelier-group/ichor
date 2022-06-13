import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Union, Optional

from ichor.core.common.functools import classproperty
from ichor.core.common.os import run_cmd
from ichor.core.common.str import split_by
from ichor.core.common.types import EnumStrList
from ichor.hpc.batch_system.batch_system import (BatchSystem, CannotParseJobID,
                                                 Job, JobID)
from ichor.hpc.batch_system.node import NodeType
from ichor.core.common.os import current_user


# todo: Make this enum available to all batch systems and each value must be specified
class JobStatus(EnumStrList):
    Running = ["R"]
    Pending = ["PD"]
    Holding = ["RH"]
    Transferring = []
    Resubmit = []
    Suspended = ["S"]
    Deleting = ["RD", "CG"]
    Error = ["F", "ST", "TO", "OOM", "NF", "BF", "CA"]


class SLURM(BatchSystem):
    """A class that implements methods ICHOR uses to submit jobs to the Sun Grid Engine (SGE) batch system. These methods/properties
    are used to construct job scripts for any program we want to run on SGE."""

    @staticmethod
    def is_present() -> bool:
        """Check if SLURM is present on the current machine ICHOR is running on."""
        return "SLURMDIR" in os.environ.keys()

    @staticmethod
    def current_node() -> NodeType:
        """Return the current type of node ichor is running on
        SLURM defines the SLURM_SUBMIT_HOST when running on a compute node
        """
        return (
            NodeType.ComputeNode
            if "SLURM_SUBMIT_HOST" in os.environ.keys()
            else NodeType.LoginNode
        )

    @classproperty
    def submit_script_command(self) -> List[str]:
        """Return a list containing command used to submit jobs to SGE batch system."""
        return ["sbatch"]

    @classmethod
    def parse_job_id(cls, stdout) -> str:
        """
        Example script submission using SLURM:
            $ sbatch test.sh
            > Submitted batch job 345234
                                  ^^^^^^
        Our job id is the final number in the stdout
        """
        try:
            return stdout.split()[-1]
        except IndexError:
            raise CannotParseJobID(
                f"Cannot parse job id from output: '{stdout}'"
            )

    @classmethod
    def get_queued_jobs(cls) -> List[Job]:
        stdout, _ = run_cmd(cls.status() + ["--array-unique", "-r"])

        jobs = []
        #     JOBID PRIORITY  PARTITION NAME            USER     ACCOUNT ST SUBMIT_TIME    START_TIME     TIME        NODES  CPUS NODELIST(REASON)
        for line in stdout.split("\n")[2:]:
            tokens = line.split()
            job_id = tokens[0] if len(tokens) >= 1 else None
            priority = tokens[1] if len(tokens) >= 2 else None
            partition = tokens[2] if len(tokens) >= 3 else None
            name = tokens[3] if len(tokens) >= 4 else None
            user = tokens[4] if len(tokens) >= 5 else None
            account = tokens[5] if len(tokens) >= 6 else None
            state = tokens[6] if len(tokens) >= 7 else None
            submit_time = tokens[7] if len(tokens) >= 8 else None
            start_time = tokens[8] if len(tokens) >= 9 else None
            time_taken = tokens[9] if len(tokens) >= 10 else None
            nodes = tokens[10] if len(tokens) >= 11 else None
            cpus = tokens[11] if len(tokens) >= 12 else None
            nodelist = tokens[12] if len(tokens) >= 13 else None

            task_id = None
            if "_" in job_id:
                job_id, task_id = job_id.split("_")
            priority = float(priority)
            state = JobStatus(state).name
            try:
                start_time = datetime.strptime(start_time, os.environ["SLURM_TIME_FORMAT"])
            except ValueError:
                start_time = None

            cpus = int(cpus)

            jobs.append(Job(
                job_id,
                priority,
                name,
                user,
                state,
                start_time,
                partition,
                cpus,
                task_id=task_id
            ))

        return jobs

    @classmethod
    def node_options(
        cls, include_nodes: List[str], exclude_nodes: List[str]
    ) -> str:
        node_options = []

        if include_nodes:
            node_options.append(f"-w {','.join(include_nodes)}")
        if exclude_nodes:
            node_options.append(f"-x {','.join(exclude_nodes)}")

        return f"\n#{cls.OptionCmd} ".join(node_options)

    @classmethod
    def hold_job(cls, job_id: Union[JobID, List[JobID]]) -> List[str]:
        """Return a list containing `hold_jid` keyword and job id which is used to hold a particular job id for it to be ran at a later time."""
        jid = (
            job_id.id
            if isinstance(job_id, JobID)
            else ":".join(map(str, [j.id for j in job_id if j is not None]))
        )
        return [f"--depend=after:{jid}"]

    @classproperty
    def delete_job_command(self) -> List[str]:
        """Return a list containing command used to delete jobs on SGE batch system."""
        return ["scancel"]

    @staticmethod
    def status() -> List[str]:
        """Return a list containing command used to check status of jobs on SGE batch system."""
        return ["squeue", "-u", f"{current_user()}"]

    @classmethod
    def change_working_directory(cls, path: Path) -> str:
        """Return the line in the job script definning the working directory from where the job is going to run."""
        return f"-D {path}"

    @classmethod
    def _get_output_fmt_str(cls, suffix: str = "o", task_array: bool = False) -> str:
        return f"%x.{suffix}%A.%a" if task_array else f"%x.{suffix}%j"

    @classmethod
    def output_directory(cls, path: Path, task_array: bool = False) -> str:
        """Return the line in the job script defining the output directory where the output of the job should be written to.
        These files end in `.o{job_id}`."""
        fmt_str = cls._get_output_fmt_str('o', task_array)
        path = path / fmt_str
        return f"-o {path}"

    @classmethod
    def error_directory(cls, path: Path, task_array: bool = False) -> str:
        """Return the line in the job script defining the error directory where any errors from the job should be written to.
        These files end in `.e{job_id}`."""
        fmt_str = cls._get_output_fmt_str('e', task_array)
        path = path / fmt_str
        return f"-e {path}"

    @classmethod
    def parallel_environment(cls, ncores: int) -> Optional[str]:
        """Returns the line in the job script defining the number of corest to be used for the job."""
        from ichor.hpc import MACHINE, PARALLEL_ENVIRONMENT

        return f"-p {PARALLEL_ENVIRONMENT[MACHINE][ncores]}\n#{cls.OptionCmd} -n {ncores}"

    @classmethod
    def array_job(cls, njobs: int, max_running_tasks: Optional[int] = None) -> str:
        """Returns the line in the job script that specifies this job is an array job. These jobs are run at the same time in parallel
        as they do not depend on one another. An example will be running 50 Gaussian or AIMALL jobs at the same time without having to submit
        50 separate jobs. Instead 1 array job can be submitted."""
        array_str = f"-a 1-{njobs}"
        if max_running_tasks is not None:
            array_str += f"{min(njobs-1, max_running_tasks)}"
        return array_str

    @classmethod
    def max_running_tasks(cls, max_running_tasks: int) -> str:
        raise NotImplementedError(f"No such command for '{cls.__class__.__name__}'")

    @classproperty
    def JobID(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SLURM_JOBID"

    @classproperty
    def TaskID(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SLURM_ARRAY_TASK_ID"

    @classproperty
    def Host(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SLURM_SUBMIT_HOST"

    @classproperty
    def TaskLast(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SLURM_ARRAY_TASK_COUNT"

    @classproperty
    def NumProcs(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SLURM_NPROCS"

    @classproperty
    def OptionCmd(self) -> str:
        """Returns the character used to define SGE options (defined at the top of the file)."""
        return "SBATCH"
