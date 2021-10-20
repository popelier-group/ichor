import multiprocessing as mp

from ichor.batch_system.batch_system import Job, JobID
from ichor.batch_system.local import LocalBatchSystem
from ichor.batch_system.node import NodeType
from ichor.batch_system.parallel_environment import ParallelEnvironments
from ichor.batch_system.sge import SunGridEngine
from ichor.machine import Machine

__all__ = ["Job", "JobID", "NodeType", "BATCH_SYSTEM", "PARALLEL_ENVIRONMENT"]

BATCH_SYSTEM = LocalBatchSystem
if SunGridEngine.is_present():
    BATCH_SYSTEM = SunGridEngine


PARALLEL_ENVIRONMENT = ParallelEnvironments()

PARALLEL_ENVIRONMENT[Machine.csf3]["smp.pe"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.ffluxlab]["smp"] = 2, 88
PARALLEL_ENVIRONMENT[Machine.local]["mp"] = 2, mp.cpu_count()
