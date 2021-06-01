from ichor.batch_system.sge import SunGridEngine
from ichor.common.functools import classproperty


class LocalBatchSystem(SunGridEngine):
    @staticmethod
    def is_present() -> bool:
        from ichor.globals import GLOBALS, Machine

        return GLOBALS.MACHINE is Machine.Local

    @classproperty
    def delete_job_command(self) -> str:
        return "echo"

    @staticmethod
    def status() -> str:
        return "echo"

    @classproperty
    def submit_script_command(self) -> str:
        return "echo"

    @classmethod
    def parse_job_id(cls, stdout) -> str:
        return "test1234"
