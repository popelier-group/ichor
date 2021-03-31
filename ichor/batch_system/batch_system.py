from abc import ABC, abstractmethod
from typing import NewType, Optional
from pathlib import Path

from ichor.common.functools import classproperty
from ichor.common.os import run_cmd
from ichor.common.io import convert_to_path

JobID = NewType("JobID", str)


class BatchSystem(ABC):
    @staticmethod
    @abstractmethod
    def is_present() -> bool:
        pass

    @classmethod
    def submit_script(cls, job_script, hold: Optional[JobID] = None) -> JobID:
        cmd = [
            cls.submit_script_command,
        ]
        if hold:
            cmd += [cls.hold_job(hold)]
        cmd += [job_script]
        stdout, _ = run_cmd(cmd)
        return stdout

    @classmethod
    @abstractmethod
    def parse_job_id(cls, stdout: str) -> JobID:
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
