import multiprocessing as mp

from ichor.batch_system.batch_system import JobID
from ichor.batch_system.parallel_environment import ParallelEnvironments
from ichor.batch_system.sge import SunGridEngine
from ichor.globals import Machine

__all__ = ["JobID", "BATCH_SYSTEM", "PARALLEL_ENVIRONMENT"]

BATCH_SYSTEM = SunGridEngine

PARALLEL_ENVIRONMENT = ParallelEnvironments()

PARALLEL_ENVIRONMENT[Machine.csf3]["smp"] = 2, 32
PARALLEL_ENVIRONMENT[Machine.ffluxlab]["smp.pe"] = 2, 44
PARALLEL_ENVIRONMENT[Machine.local]["mp"] = 2, mp.cpu_count()
