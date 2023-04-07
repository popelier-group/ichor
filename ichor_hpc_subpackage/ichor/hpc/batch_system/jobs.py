import contextlib
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Union

from ichor.core.common.io import mkdir
from ichor.core.common.types import VarReprMixin


class CannotParseJobID(Exception):
    pass


class JobID:
    """Class used to keep track of jobs submitted to compute nodes.

    :param script: A path to a script file such as GAUSSIAN.sh
        that will be submitted to compute node.
    :param id: The job id given to the job when the job was submitted to a compute node.
    :instance: the unique identified (UUID) that is used for the job's
    datafile (containing the names of all the files needed for the job).
    """

    def __init__(self, script: Union[str, Path], id: str):
        self.script = str(script)
        self.id = id

    def write(self):
        from ichor.hpc import FILE_STRUCTURE

        mkdir(
            FILE_STRUCTURE["jid"].parent
        )  # make parent directories if they don't exist

        job_ids = []
        # if the jid file exists (which contains queued jobs), then read it and append to job_ids list
        if FILE_STRUCTURE["jid"].exists():
            with open(FILE_STRUCTURE["jid"], "r") as f:
                with contextlib.suppress(json.JSONDecodeError):
                    job_ids += json.load(f)
        job_ids += [
            {
                "script": self.script,
                "id": self.id,
                # "instance": self.instance,
            }
        ]

        # overwrite the jobs file, writing out any new jobs that were
        # submitted plus the old jobs that were already in the file.
        with open(FILE_STRUCTURE["jid"], "w") as f:
            json.dump(job_ids, f)

    def __repr__(self) -> str:
        return f"JobID(script: {self.script}, id: {self.id}."


class Job(VarReprMixin):
    def __init__(
        self,
        id: str,
        priority: float,
        name: str,
        user: str,
        state: str,
        start: datetime,
        queue: str,
        slots: int,
        task_id: Optional[str] = None,
    ):
        self.id = id
        self.priority = priority
        self.name = name
        self.user = user
        self.state = state
        self.start = start
        self.queue = queue
        self.slots = slots
        self.task_id = task_id
