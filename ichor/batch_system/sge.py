import os
import re
from pathlib import Path

from ichor.batch_system.batch_system import BatchSystem, JobID
from ichor.common.functools import classproperty
from ichor.common.io import convert_to_path


class SunGridEngine(BatchSystem):
    @staticmethod
    def is_present() -> bool:
        return "SGE_ROOT" in os.environ.keys()

    @classproperty
    def submit_script_command(self) -> str:
        return "qsub"

    @classmethod
    def parse_job_id(cls, stdout) -> str:
        return re.findall(r"\d+", stdout)[0]

    @classmethod
    def hold_job(cls, job_id: JobID):
        return ["-hold_jid", f"{job_id.id}"]

    @classproperty
    def delete_job_command(self) -> str:
        return "qdel"

    @staticmethod
    def status() -> str:
        return "qstat"

    @classmethod
    def change_working_directory(cls, path: Path) -> str:
        return f"-wd {path}"

    @classmethod
    def output_directory(cls, path: Path) -> str:
        return f"-o {path}"

    @classmethod
    def error_directory(cls, path: Path) -> str:
        return f"-e {path}"

    @classmethod
    def parallel_environment(cls, ncores: int) -> str:
        from ichor.batch_system import PARALLEL_ENVIRONMENT
        from ichor.globals import GLOBALS

        return f"-pe {PARALLEL_ENVIRONMENT[GLOBALS.MACHINE][ncores]} {ncores}"

    @classmethod
    def array_job(cls, njobs: int) -> str:
        return f"-t 1-{njobs}"

    @classproperty
    def JobID(self) -> str:
        return "JOB_ID"

    @classproperty
    def TaskID(self) -> str:
        return "SGE_TASK_ID"

    @classproperty
    def TaskLast(self) -> str:
        return "SGE_TASK_LAST"

    @classproperty
    def NumProcs(self) -> str:
        return "NSLOTS"

    @classproperty
    def OptionCmd(self) -> str:
        return "$"
