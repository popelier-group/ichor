from ichor.ichor_hpc.batch_system.batch_system import Job, JobID
from ichor.ichor_hpc.batch_system.local import LocalBatchSystem
from ichor.ichor_hpc.batch_system.node import NodeType
from ichor.ichor_hpc.batch_system.sge import SunGridEngine

__all__ = ["Job", "JobID", "NodeType", "BATCH_SYSTEM"]

BATCH_SYSTEM = LocalBatchSystem
if SunGridEngine.is_present():
    BATCH_SYSTEM = SunGridEngine
