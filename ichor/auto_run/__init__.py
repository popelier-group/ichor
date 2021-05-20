from enum import Enum
from typing import Callable, Optional, Sequence, Any

from ichor.auto_run.aimall import auto_run_aimall
from ichor.auto_run.ferebus import auto_run_ferebus
from ichor.auto_run.gaussian import auto_run_gaussian
from ichor.auto_run.ichor import (adaptive_sampling, make_models, submit_gjfs,
                                  submit_wfns)
from ichor.batch_system import JobID

__all__ = [
    "auto_run_gaussian",
    "auto_run_aimall",
    "auto_run_ferebus",
    "submit_gjfs",
    "submit_wfns",
    "make_models",
    "adaptive_sampling",
]


class IterState(Enum):
    First = 1
    Standard = 2
    Last = 3


class IterUsage(Enum):
    All = 1
    AllButLast = 2

    def __contains__(self, state: IterState):
        return self is not IterUsage.AllButLast or state is not IterState.Last


class IterArgs:
    from ichor.globals import GLOBALS

    TrainingSetLocation = GLOBALS.FILE_STRUCTURE["training_set"]
    SamplePoolLocation = GLOBALS.FILE_STRUCTURE["sample_pool"]
    FerebusDirectory = GLOBALS.FILE_STRUCTURE["models"]
    ModelLocation = GLOBALS.FILE_STRUCTURE["ferebus"]

    Atoms = [atom.name for atom in GLOBALS.ATOMS] if GLOBALS.OPTIMISE_ATOM == "all" else [GLOBALS.OPTIMISE_ATOM]


class IterStep:
    func: Callable
    usage: IterUsage
    args: Sequence[Any]

    def __init__(self, func, usage, args):
        self.func = func
        self.usage = usage
        self.args = args

    def run(self, wait_for_job: Optional[JobID], state: IterState) -> Optional[JobID]:
        if state in self.usage:
            return self.func(*[arg.value for arg in self.args], hold=wait_for_job)


func_order = [
    IterStep(
        submit_gjfs,
        IterUsage.All,
        (IterArgs.TrainingSetLocation)
    ),
    IterStep(
        auto_run_gaussian,
        IterUsage.All,
        (IterArgs.TrainingSetLocation)
    ),
    IterStep(
        submit_wfns,
        IterUsage.All,
        (IterArgs.TrainingSetLocation, IterArgs.Atoms)
    ),
    IterStep(
        auto_run_aimall,
        IterUsage.All,
        (IterArgs.TrainingSetLocation, IterArgs.Atoms)
    ),
    IterStep(
        make_models,
        IterUsage.All,
        (IterArgs.TrainingSetLocation, IterArgs.Atoms),
    ),
    IterStep(
        auto_run_ferebus,
        IterUsage.All,
        (IterArgs.FerebusDirectory, IterArgs.Atoms)
    ),
    IterStep(
        adaptive_sampling,
        IterUsage.AllButLast,
        (IterArgs.ModelLocation, IterArgs.SamplePoolLocation),
    ),
]


def next_iter(wait_for_job: Optional[JobID], state: IterState = IterState.Standard) -> Optional[JobID]:
    job_id = wait_for_job
    for iter_step in func_order:
        job_id = iter_step.run(job_id, state)
    return job_id


def auto_run():
    from ichor.globals import GLOBALS

    iterations = [IterState.Standard for _ in range(GLOBALS.N_ITERATIONS)]
    iterations[0] = IterState.First
    iterations += [IterState.Last]

    job_id = None
    for iter_state in iterations:
        job_id = next_iter(job_id, iter_state)
