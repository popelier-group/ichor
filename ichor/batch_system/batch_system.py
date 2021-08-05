import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union, List

from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.common.os import run_cmd


class JobID:
    script: str
    id: str
    instance: str

    def __init__(
        self, script: Union[str, Path], id: str, instance: Optional[str] = None
    ):
        self.script = str(script)
        self.id = str(id)
        from ichor.globals import GLOBALS

        self.instance = instance or str(GLOBALS.UID)

    def write(self):
        from ichor.globals import GLOBALS

        mkdir(GLOBALS.FILE_STRUCTURE["jid"].parent)

        job_ids = []
        if GLOBALS.FILE_STRUCTURE["jid"].exists():
            with open(GLOBALS.FILE_STRUCTURE["jid"], "r") as f:
                job_ids += json.load(f)

        job_ids += [
            {
                "script": str(self.script),
                "id": str(self.id),
                "instance": str(self.instance),
            }
        ]

        with open(GLOBALS.FILE_STRUCTURE["jid"], "w") as f:
            json.dump(job_ids, f)

    def __repr__(self) -> str:
        return f"JobID(Script: {self.script}, Id: {self.id}, Instance: {self.instance})"


class BatchSystem(ABC):
    @staticmethod
    @abstractmethod
    def is_present() -> bool:
        pass

    @classmethod
    def submit_script(
        cls, job_script: Path, hold: Optional[JobID] = None
    ) -> JobID:
        cmd = cls.submit_script_command
        if hold:
            cmd += cls.hold_job(hold)
        cmd += [job_script]

        stdout, stderr = run_cmd(cmd)
        job_id = JobID(job_script, cls.parse_job_id(stdout))
        job_id.write()
        return job_id

    @classmethod
    def delete(cls, job: JobID):
        cmd = cls.delete_job_command + [job.id]
        stdout, stderr = run_cmd(cmd)

    @classmethod
    @abstractmethod
    def parse_job_id(cls, stdout: str) -> str:
        pass

    @classmethod
    @abstractmethod
    def hold_job(cls, job: JobID):
        pass

    @classproperty
    @abstractmethod
    def submit_script_command(self) -> List[str]:
        pass

    @classmethod
    def delete_job(cls, job_id: JobID) -> None:
        cmd = [cls.delete_job_command, job_id]
        stdout, _ = run_cmd(cmd)
        return stdout

    @classproperty
    @abstractmethod
    def delete_job_command(self) -> List[str]:
        pass

    @staticmethod
    @abstractmethod
    def status() -> str:
        pass

    @classmethod
    @abstractmethod
    def change_working_directory(cls, path: Path) -> str:
        pass

    @classmethod
    @abstractmethod
    def output_directory(cls, path: Path) -> str:
        pass

    @classmethod
    @abstractmethod
    def error_directory(cls, path: Path) -> str:
        pass

    @classmethod
    @abstractmethod
    def parallel_environment(cls, ncores: int) -> str:
        pass

    @classmethod
    @abstractmethod
    def array_job(cls, njobs: int) -> str:
        pass

    @classproperty
    @abstractmethod
    def JobID(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def TaskID(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def TaskLast(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def NumProcs(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def OptionCmd(self) -> str:
        pass
