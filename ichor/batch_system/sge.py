import os
import re
from pathlib import Path

from ichor.batch_system.batch_system import BatchSystem, JobID
from ichor.common.functools import classproperty
from ichor.common.io import convert_to_path


class SunGridEngine(BatchSystem):
    def is_present(self) -> bool:
        return "SGE_ROOT" in os.environ.keys()

    @classproperty
    def submit_script_command(self) -> str:
        return "qsub"

    @classproperty
    def parse_job_id(cls, stdout) -> JobID:
        return JobID(re.findall(r"\d+", stdout)[0])

    @classmethod
    def hold_job(cls, job_id: JobID):
        return f"-hold_jib {job_id}"

    @classproperty
    def delete_job_command(self) -> str:
        return "qdel"

    @staticmethod
    def status() -> str:
        return "qstat"

    @classmethod
    @convert_to_path
    def change_working_directory(cls, path: Path) -> str:
        return f"-wd {path}"

    @classmethod
    def parallel_environment(cls, ncores: int) -> str:


    @classproperty
    def JobID(self) -> str:
        return "JOB_ID"

    @classproperty
    def TaskID(self) -> str:
        return "SGE_TASK_ID"

    @classproperty
    def NumProcs(self) -> str:
        return "NSLOTS"

    @classproperty
    def OptionCmd(self) -> str:
        return "$"
