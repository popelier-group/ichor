from typing import List

from ichor.ichor_hpc.batch_system.node import NodeType
from ichor.ichor_hpc.batch_system.sge import SunGridEngine
from ichor.ichor_lib.common.functools import classproperty


class LocalBatchSystem(SunGridEngine):
    """LocalBatchSystem is to only be used for debugging purposes
    (Unless one wants to implement a batch system to run on a local machine... would be a nice addition)"""

    @staticmethod
    def is_present() -> bool:
        from ichor.ichor_hpc.machine_setup.machine_setup import MACHINE, Machine

        return MACHINE is Machine.Local

    @staticmethod
    def current_node() -> NodeType:
        return NodeType.LoginNode

    @classproperty
    def delete_job_command(self) -> List[str]:
        return ["echo"]

    @staticmethod
    def status() -> List[str]:
        return ["echo"]

    @classproperty
    def submit_script_command(self) -> List[str]:
        return ["echo"]

    @classmethod
    def parse_job_id(cls, stdout) -> List[str]:
        return ["test1234"]