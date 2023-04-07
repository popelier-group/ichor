from ichor.hpc.batch_system.jobs import Job, JobID
from ichor.hpc.batch_system.local import LocalBatchSystem
from ichor.hpc.batch_system.node import NodeType
from ichor.hpc.batch_system.parallel_environment import (
    ParallelEnvironment,
    ParallelEnvironments,
)
from ichor.hpc.batch_system.sge import SunGridEngine
from ichor.hpc.batch_system.slurm import SLURM


def init_batch_system():

    if SunGridEngine.is_present():
        batch_system = SunGridEngine
    if SLURM.is_present():
        batch_system = SLURM
    else:
        batch_system = LocalBatchSystem
    return batch_system


__all__ = [
    "Job",
    "JobID",
    "LocalBatchSystem",
    "NodeType",
    "ParallelEnvironment",
    "ParallelEnvironments",
    "SunGridEngine",
    "SLURM",
    "init_batch_system",
]
