from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union

from ichor.common.functools import classproperty
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
        cmd = [
            cls.submit_script_command,
        ]
        if hold:
            cmd += [cls.hold_job(hold)]
        cmd += [job_script]
        from ichor.globals import GLOBALS, Machine

        stdout, _ = (
            run_cmd(cmd) if GLOBALS.MACHINE is not Machine.local else "1234",
            "",
        )
        job_id = cls.parse_job_id(stdout)
        return JobID(job_script, job_id)

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
    def submit_script_command(self) -> str:
        pass

    @classmethod
    def delete_job(cls, job_id: JobID) -> None:
        cmd = [cls.delete_job_command, job_id]
        stdout, _ = run_cmd(cmd)
        return stdout

    @classproperty
    @abstractmethod
    def delete_job_command(self) -> str:
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
    def NumProcs(self) -> str:
        pass

    @classproperty
    @abstractmethod
    def OptionCmd(self) -> str:
        pass
