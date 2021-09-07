from enum import Enum
from typing import Any, Callable, Optional, Sequence

from ichor.auto_run.auto_run_aimall import submit_aimall_job_to_auto_run
from ichor.auto_run.auto_run_ferebus import submit_ferebus_job_to_auto_run
from ichor.auto_run.auto_run_gaussian import submit_gaussian_job_to_auto_run
from ichor.auto_run.ichor import (make_models,
                                  submit_ichor_active_learning_job_to_auto_run,
                                  submit_ichor_aimall_command_to_auto_run,
                                  submit_ichor_gaussian_command_to_auto_run,
                                  submit_make_sets_job_to_auto_run)
from ichor.auto_run.in_auto_run import AutoRunOnly
from ichor.batch_system import JobID
from ichor.common.io import mkdir
from ichor.common.int import truncate
from ichor.common.points import get_points_location
from ichor.common.types import MutableValue
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import Trajectory
from ichor.machine import MACHINE, SubmitType
from ichor.make_sets import make_sets_npoints
from ichor.points import PointsDirectory
from ichor.submission_script import DataLock, SCRIPT_NAMES
from ichor.drop_compute import DROP_COMPUTE_LOCATION

__all__ = [
    "submit_gaussian_job_to_auto_run",
    "submit_aimall_job_to_auto_run",
    "submit_ferebus_job_to_auto_run",
    "submit_ichor_gaussian_command_to_auto_run",
    "submit_ichor_aimall_command_to_auto_run",
    "make_models",
    "submit_ichor_active_learning_job_to_auto_run",
    "auto_run",
    "AutoRunOnly",
]


class AutoRunAlreadyRunning(Exception):
    pass


class IterState(Enum):
    """The iteration which the adaptive sampling is on. The first step is making the sets (running Makeset)."""

    First = 1
    Standard = 2
    Last = 3


class IterUsage(Enum):
    """Tells the IterStep wheter or not it can be run given an IterState"""

    First = 0
    All = 1
    AllButLast = 2

    def __contains__(self, state: IterState):
        return self is not IterUsage.AllButLast or state is not IterState.Last


class IterArgs:
    """Various arguments which need to be defined for a job to run successfully."""

    TrainingSetLocation = FILE_STRUCTURE["training_set"]
    SamplePoolLocation = FILE_STRUCTURE["sample_pool"]
    FerebusDirectory = FILE_STRUCTURE["ferebus"]
    ModelLocation = FILE_STRUCTURE["models"]
    nPoints = MutableValue(1)  # Overwritten Based On IterState
    Atoms = MutableValue([])  # Overwritten from GLOBALS.ATOMS


class IterStep:
    """A class which wraps around each step of one iteration (each iteration has Guassian, AIMALL, FEREBUS, and ICHOR steps)."""

    func: Callable
    usage: IterUsage
    args: Sequence[Any]

    def __init__(self, func: Callable, usage: IterUsage, args: Sequence[Any]):
        self.func = func
        self.usage = usage
        self.args = args

    def run(
        self, wait_for_job: Optional[JobID], state: IterState
    ) -> Optional[JobID]:
        if state in self.usage:
            return self.func(*self.args, hold=wait_for_job)


# order in which to submit jobs for each of the adaptive sampling iterations.
func_order = [
    IterStep(
        submit_ichor_gaussian_command_to_auto_run,
        IterUsage.All,
        [IterArgs.TrainingSetLocation],
    ),
    IterStep(
        submit_gaussian_job_to_auto_run, IterUsage.All, [IterArgs.nPoints]
    ),
    IterStep(
        submit_ichor_aimall_command_to_auto_run,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms],
    ),
    IterStep(
        submit_aimall_job_to_auto_run,
        IterUsage.All,
        [IterArgs.nPoints, IterArgs.Atoms],
    ),
    IterStep(
        make_models,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms],
    ),
    IterStep(
        submit_ferebus_job_to_auto_run,
        IterUsage.All,
        [IterArgs.FerebusDirectory, IterArgs.Atoms],
    ),
    IterStep(
        submit_ichor_active_learning_job_to_auto_run,
        IterUsage.AllButLast,
        [IterArgs.ModelLocation, IterArgs.SamplePoolLocation],
    ),
]


def next_iter(
    wait_for_job: Optional[JobID], state: IterState = IterState.Standard
) -> Optional[JobID]:
    from ichor.globals import GLOBALS

    # the first submitted job does not wait for previous jobs (because there are none), so job_id is None
    job_id = wait_for_job

    # the first job will execute this since the first iteration is IterState.First
    if state == IterState.First:
        if IterArgs.TrainingSetLocation.exists():
            IterArgs.nPoints.value = len(
                PointsDirectory(IterArgs.TrainingSetLocation)
            )
        else:
            points_location = (
                get_points_location()
            )  # get points location on disk to transform into ListOfAtoms
            points = None
            # points_location could be a directory of points to use, if so initialise a PointsDirectory
            if points_location.is_dir():
                points = PointsDirectory(points_location)
            # points_location could be a .xyz file, if so initialise a Trajectory
            elif points_location.suffix == ".xyz":
                points = Trajectory(points_location)
            else:
                raise ValueError("Unknown Points Location")

            # return the total number of points which are going to be in the initial training set
            IterArgs.nPoints.value = make_sets_npoints(
                points, GLOBALS.TRAINING_POINTS, GLOBALS.TRAINING_SET_METHOD
            )
            # run the make_sets function on a compute node, which makes the training and sample pool sets from the points_location
            job_id = IterStep(
                submit_make_sets_job_to_auto_run,
                IterUsage.All,
                [points_location],
            ).run(job_id, state)
            print(f"Submitted: {job_id}")

    # for every other job, i.e. IterState.Standard, IterState.Last
    else:
        IterArgs.nPoints.value = GLOBALS.POINTS_PER_ITERATION

    if GLOBALS.OPTIMISE_ATOM == "all":
        IterArgs.Atoms.value = [atom.name for atom in GLOBALS.ATOMS]
    else:
        IterArgs.Atoms.value = [GLOBALS.OPTIMISE_ATOM]

    modify_id = truncate(GLOBALS.UID.int, nbits=32)  # only used for drop-n-compute

    for iter_step in func_order:
        if MACHINE.submit_type is SubmitType.DropCompute:
            modify = f"+{modify_id}"
            if job_id is not None:
                modify += f"+hold_{modify_id - 1}"
            SCRIPT_NAMES.modify = modify
            modify_id += 1
        job_id = iter_step.run(job_id, state)
        if job_id is not None:
            print(f"Submitted: {job_id}")
    return job_id


def auto_run() -> Optional[JobID]:
    """Auto run Gaussian, AIMALL, FEREBUS, and ICHOR jobs needed to make GP models."""
    from ichor.globals import GLOBALS

    if FILE_STRUCTURE["counter"].exists():
        raise AutoRunAlreadyRunning(
            f"Auto Run may already be running, as {FILE_STRUCTURE['counter']} exists\nIf this is a mistake, remove {FILE_STRUCTURE['counter']} and retry"
        )

    mkdir(FILE_STRUCTURE["counter"].parent)
    with open(FILE_STRUCTURE["counter"], "w") as f:
        f.write("0")

    # Make a list of types of iterations. Only first and last iterations are different.
    iterations = [IterState.Standard for _ in range(GLOBALS.N_ITERATIONS)]
    iterations[0] = IterState.First
    iterations += [
        IterState.Last
    ]  # The IterState.Last informs the active learning IterStep to not run on the final iteration as it has IterUsage.AllButLast

    job_id = None
    with DataLock():
        for i, iter_state in enumerate(iterations):
            print(f"Submitting Iter: {i+1}")
            # initially job_id is none, then next_iter returns the job id of the submitted job. The next job has to wait for the previous job that was submitted.
            job_id = next_iter(job_id, iter_state)

            if MACHINE.submit_type is SubmitType.DropCompute:
                break  # Only submit the first iteration for drop-n-compute
    return job_id


def submit_next_iter(current_iteration) -> Optional[JobID]:
    from ichor.globals import GLOBALS

    if MACHINE.submit_type is SubmitType.DropCompute:
        SCRIPT_NAMES.parent = DROP_COMPUTE_LOCATION

    iter_state = IterState.Last if current_iteration == GLOBALS.N_ITERATIONS else IterState.Standard
    return next_iter(None, iter_state)
