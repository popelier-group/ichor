import os
import re
from datetime import datetime
from pathlib import Path
from typing import List, Union

from ichor.batch_system.batch_system import (BatchSystem, CannotParseJobID,
                                             Job, JobID)
from ichor.batch_system.node import NodeType
from ichor.common.functools import classproperty
from ichor.common.os import run_cmd
from ichor.common.str import split_by
from ichor.common.types import EnumStrList


class JobStatus(EnumStrList):
    Running = ["r"]
    Pending = ["qw"]
    Holding = ["hqw", "hRqw"]
    Transferring = ["t"]
    Resubmit = ["Rr", "Rt"]
    Suspended = ["s"]
    Deleting = [
        "dr",
        "dt",
        "dRr",
        "dRt",
        "ds",
        "dS",
        "dT",
        "dRs",
        "dRS",
        "dRT",
    ]
    Error = ["Eqw", "Ehqw", "EhRqw"]


class SunGridEngine(BatchSystem):
    """A class that implements methods ICHOR uses to submit jobs to the Sun Grid Engine (SGE) batch system. These methods/properties
    are used to construct job scripts for any program we want to run on SGE."""

    @staticmethod
    def is_present() -> bool:
        """Check if SGE is present on the current machine ICHOR is running on."""
        return "SGE_ROOT" in os.environ.keys()

    @staticmethod
    def current_node() -> NodeType:
        """Return the current type of node ichor is running on
        SGE defines the SGE_O_HOST when running on a compute node
        """
        return (
            NodeType.ComputeNode
            if "SGE_O_HOST" in os.environ.keys()
            else NodeType.LoginNode
        )

    @classproperty
    def submit_script_command(self) -> List[str]:
        """Return a list containing command used to submit jobs to SGE batch system."""
        return ["qsub"]

    @classmethod
    def parse_job_id(cls, stdout) -> str:
        """
        Example script submission using SGE:
            $ qsub test.sh
            > Your job 518753 ("test.sh") has been submitted

        Our job id is given by the number, this is parsed by finding the number in the return string
        """
        try:
            return re.findall(r"\d+", stdout)[0]
        except IndexError:
            raise CannotParseJobID(
                f"Cannot parse job id from output: '{stdout}'"
            )

    @classmethod
    def get_queued_jobs(cls) -> List[Job]:
        stdout, _ = run_cmd(["qstat"])

        jobs = []
        # job-ID  prior   name       user         state submit/start at     queue                          slots ja-task-ID
        # -----------------------------------------------------------------------------------------------------------------
        for line in stdout.split("\n")[2:]:
            (
                job_id,
                priority,
                name,
                user,
                state,
                start,
                queue,
                slots,
                tasks,
            ) = split_by(
                line,
                [8, 8, 11, 13, 6, 20, 31, 6],
                strip=True,
                return_remainder=True,
            )
            priority = float(priority)
            state = JobStatus(state).name
            start = datetime.strptime(start, "%d/%m/%Y %H:%M:%S")
            slots = int(slots)
            if tasks:
                if "-" in tasks:
                    s, f = tasks.split(":")[0].split("-")
                    s, f = int(s), int(f)
                    jobs += [
                        Job(
                            job_id,
                            priority,
                            name,
                            user,
                            state,
                            start,
                            queue,
                            slots,
                            task_id=str(i),
                        )
                        for i in range(s, f)
                    ]
                else:
                    jobs += [
                        Job(
                            job_id,
                            priority,
                            name,
                            user,
                            state,
                            start,
                            queue,
                            slots,
                            task_id=tasks,
                        )
                    ]
            else:
                jobs += [
                    Job(
                        job_id,
                        priority,
                        name,
                        user,
                        state,
                        start,
                        queue,
                        slots,
                        task_id="1",
                    )
                ]
        return jobs

    @classmethod
    def hold_job(cls, job_id: Union[JobID, List[JobID]]) -> List[str]:
        """Return a list containing `hold_jid` keyword and job id which is used to hold a particular job id for it to be ran at a later time."""
        jid = (
            job_id.id
            if isinstance(job_id, JobID)
            else ",".join(map(str, [j.id for j in job_id if j is not None]))
        )
        return ["-hold_jid", f"{jid}"]

    @classproperty
    def delete_job_command(self) -> List[str]:
        """Return a list containing command used to delete jobs on SGE batch system."""
        return ["qdel"]

    @staticmethod
    def status() -> List[str]:
        """Return a list containing command used to check status of jobs on SGE batch system."""
        return ["qstat"]

    @classmethod
    def change_working_directory(cls, path: Path) -> str:
        """Return the line in the job script definning the working directory from where the job is going to run."""
        return f"-wd {path}"

    @classmethod
    def output_directory(cls, path: Path) -> str:
        """Return the line in the job script defining the output directory where the output of the job should be written to.
        These files end in `.o{job_id}`."""
        return f"-o {path}"

    @classmethod
    def error_directory(cls, path: Path) -> str:
        """Return the line in the job script defining the error directory where any errors from the job should be written to.
        These files end in `.e{job_id}`."""
        return f"-e {path}"

    @classmethod
    def parallel_environment(cls, ncores: int) -> str:
        """Returns the line in the job script defining the number of corest to be used for the job."""
        from ichor.parallel_environment import PARALLEL_ENVIRONMENT
        from ichor.machine import MACHINE

        return f"-pe {PARALLEL_ENVIRONMENT[MACHINE][ncores]} {ncores}"

    @classmethod
    def array_job(cls, njobs: int) -> str:
        """Returns the line in the job script that specifies this job is an array job. These jobs are run at the same time in parallel
        as they do not depend on one another. An example will be running 50 Gaussian or AIMALL jobs at the same time without having to submit
        50 separate jobs. Instead 1 array job can be submitted."""
        return f"-t 1-{njobs}"

    @classproperty
    def JobID(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "JOB_ID"

    @classproperty
    def TaskID(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SGE_TASK_ID"

    @classproperty
    def Host(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SGE_O_HOST"

    @classproperty
    def TaskLast(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "SGE_TASK_LAST"

    @classproperty
    def NumProcs(self) -> str:
        """https://docs.oracle.com/cd/E19957-01/820-0699/chp4-21/index.html"""
        return "NSLOTS"

    @classproperty
    def OptionCmd(self) -> str:
        """Returns the character used to define SGE options (defined at the top of the file)."""
        return "$"
