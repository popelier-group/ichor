""" Standard auto run implementation which runs iteration containing Gaussian, FEREBUS, jobs"""


from enum import Enum
from pathlib import Path
from typing import Any, Callable, List, Optional, Sequence

from ichor.auto_run.auto_run_aimall import submit_aimall_job_to_auto_run
from ichor.auto_run.auto_run_ferebus import submit_ferebus_job_to_auto_run
from ichor.auto_run.auto_run_gaussian import submit_gaussian_job_to_auto_run
from ichor.auto_run.auto_run_morfi import submit_morfi_job_to_auto_run
from ichor.auto_run.auto_run_pyscf import submit_pyscf_job_to_auto_run
from ichor.auto_run.ichor_jobs import (
    make_models, submit_ichor_active_learning_job_to_auto_run,
    submit_ichor_aimall_command_to_auto_run,
    submit_ichor_gaussian_command_to_auto_run,
    submit_ichor_morfi_command_to_auto_run,
    submit_ichor_pyscf_command_to_auto_run, submit_make_sets_job_to_auto_run)
from ichor.batch_system import JobID
from ichor.common.int import truncate
from ichor.common.io import mkdir, remove
from ichor.common.points import get_points_location
from ichor.common.types import MutableValue
from ichor.drop_compute import DROP_COMPUTE_LOCATION
from ichor.file_structure import FILE_STRUCTURE
from ichor.files import PointsDirectory, Trajectory
from ichor.machine import MACHINE, SubmitType
from ichor.main.queue import get_current_jobs
from ichor.make_sets import make_sets_npoints
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram
from ichor.qct import (QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
                       QuantumChemicalTopologyProgram)
from ichor.submission_script import SCRIPT_NAMES, DataLock
from ichor.auto_run.counter import read_counter, write_counter
from ichor.batch_system import BATCH_SYSTEM, NodeType


class AutoRunAlreadyRunning(Exception):
    pass


class IterState(Enum):
    """The iteration which the adaptive sampling is on. The first step is making the sets (running Makeset)."""

    First = 1
    Standard = 2
    Last = 3


class IterUsage(Enum):
    """Tells the IterStep whether or not it can be run given an IterState"""

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
    ModelTypes = MutableValue([])


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
        else:
            return wait_for_job


def submit_auto_run_iter(
    func_order: List[IterStep],
    wait_for_job: Optional[JobID] = None,
    state: IterState = IterState.Standard,
) -> Optional[JobID]:
    from ichor.globals import GLOBALS

    # the first submitted job does not wait for previous jobs (because there are none), so job_id is None
    job_id = wait_for_job

    modify_id = ""
    if MACHINE.submit_type is SubmitType.DropCompute:
        # modify the uid for drop-n-compute as SGE is 32-bit
        modify_id = truncate(
            GLOBALS.UID.int, nbits=32
        )  # only used for drop-n-compute
        if modify_id >= 2 ** 32 - len(func_order):  # overflow protection
            modify_id -= len(func_order)

    with DataLock():
        job_id = None
        # Other jobs will be IterState.Standard (apart from IterState.Last), thus we run the sequence of jobs specified in func_order
        for iter_step in func_order:
            # append the modified id to the submission script name as this is how drop-in-compute holds jobs
            if MACHINE.submit_type is SubmitType.DropCompute and BATCH_SYSTEM.current_node() is NodeType.ComputeNode:
                modify = f"+{modify_id}"
                if job_id is not None:
                    modify += f"+hold_{modify_id - 1}"  # hold for the previous job (whose job id is one less than this job)
                SCRIPT_NAMES.modify.value = modify
                modify_id += 1
            job_id = iter_step.run(job_id, state)
            if job_id is not None:
                print(f"Submitted: {job_id}")

    # always return the job_id at the end because we need to hold next jobs
    return job_id


def get_qcp_steps():
    QCP = QUANTUM_CHEMISTRY_PROGRAM()
    if QCP is QuantumChemistryProgram.Gaussian:
        ichor_qcp_function = submit_ichor_gaussian_command_to_auto_run
        qcp_function = submit_gaussian_job_to_auto_run
    elif QCP is QuantumChemistryProgram.PySCF:
        ichor_qcp_function = submit_ichor_pyscf_command_to_auto_run
        qcp_function = submit_pyscf_job_to_auto_run
    else:
        raise ValueError(
            f"Cannot run Quantum Chemistry Program '{QCP.name}' in auto-run"
        )

    ichor_qcp_step = IterStep(
        ichor_qcp_function,
        IterUsage.All,
        [IterArgs.TrainingSetLocation],
    )
    qcp_step = IterStep(qcp_function, IterUsage.All, [IterArgs.nPoints])

    return ichor_qcp_step, qcp_step


def get_qct_steps():
    QCTP = QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM()
    if QCTP is QuantumChemicalTopologyProgram.AIMAll:
        ichor_qct_function = submit_ichor_aimall_command_to_auto_run
        qct_function = submit_aimall_job_to_auto_run
    elif QCTP is QuantumChemicalTopologyProgram.Morfi:
        ichor_qct_function = submit_ichor_morfi_command_to_auto_run
        qct_function = submit_morfi_job_to_auto_run
    else:
        raise ValueError(
            f"Cannot run Quantum Chemical Topology Program '{QCTP.name}' in auto-run"
        )

    ichor_qct_step = IterStep(
        ichor_qct_function,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms],
    )

    qct_step = IterStep(
        qct_function,
        IterUsage.All,
        [IterArgs.nPoints, IterArgs.Atoms],
    )

    return ichor_qct_step, qct_step


def get_model_steps():
    make_models_step = IterStep(
        make_models,
        IterUsage.All,
        [IterArgs.TrainingSetLocation, IterArgs.Atoms, IterArgs.ModelTypes],
    )
    ferebus_step = IterStep(
        submit_ferebus_job_to_auto_run,
        IterUsage.All,
        [IterArgs.FerebusDirectory, IterArgs.Atoms],
    )

    return make_models_step, ferebus_step


def get_func_order():
    # order in which to submit jobs for each of the adaptive sampling iterations.
    return [
        *get_qcp_steps(),
        *get_qct_steps(),
        *get_model_steps(),
        IterStep(
            submit_ichor_active_learning_job_to_auto_run,
            IterUsage.AllButLast,
            [IterArgs.ModelLocation, IterArgs.SamplePoolLocation],
        ),
    ]


def auto_run() -> JobID:
    """Auto run Gaussian, AIMALL, FEREBUS, and ICHOR jobs needed to make GP models."""
    from ichor.globals import GLOBALS

    if FILE_STRUCTURE["counter"].exists():
        current_iter, max_iter = read_counter()

        if current_iter < max_iter:
            raise AutoRunAlreadyRunning(
                f"Auto Run may already be running, as {FILE_STRUCTURE['counter']} exists and {current_iter} < {max_iter}\nIf this is a mistake, remove {FILE_STRUCTURE['counter']} and retry"
            )

    write_counter(0, GLOBALS.N_ITERATIONS)

    # Make a list of types of iterations. Only first and last iterations are different.
    iterations = [IterState.Standard for _ in range(GLOBALS.N_ITERATIONS)]
    iterations[0] = IterState.First
    iterations += [
        IterState.Last
    ]  # The IterState.Last informs the active learning IterStep to not run on the final iteration as it has IterUsage.AllButLast

    func_order = get_func_order()

    if GLOBALS.OPTIMISE_ATOM == "all":
        IterArgs.Atoms.value = [atom.name for atom in GLOBALS.ATOMS]
    else:
        IterArgs.Atoms.value = [GLOBALS.OPTIMISE_ATOM]

    if GLOBALS.OPTIMISE_PROPERTY == "all":
        from ichor.main.make_models import MODEL_TYPES

        IterArgs.ModelTypes.value = MODEL_TYPES
    else:
        types = GLOBALS.OPTIMISE_PROPERTY
        if isinstance(types, str):
            types = [types]
        IterArgs.ModelTypes.value = types

    job_id = None
    with DataLock():
        for i, iter_state in enumerate(iterations):
            # the first job will execute this since the first iteration is IterState.First
            if iter_state is IterState.First:
                if IterArgs.TrainingSetLocation.exists():
                    IterArgs.nPoints.value = len(
                        PointsDirectory(IterArgs.TrainingSetLocation)
                    )
                else:
                    points_location = (
                        get_points_location()
                    )  # get points location on disk to transform into ListOfAtoms
                    # points_location could be a directory of points to use, if so initialise a PointsDirectory
                    if points_location.is_dir():
                        points = PointsDirectory(points_location)
                    # points_location could be a .xyz file, if so initialise a Trajectory
                    elif points_location.suffix == ".xyz":
                        points = Trajectory(points_location)
                    else:
                        raise ValueError("Unknown Points Location")

                    print(f"Submitting Make Sets using {points_location}")
                    # return the total number of points which are going to be in the initial training set
                    IterArgs.nPoints.value = make_sets_npoints(
                        points,
                        GLOBALS.TRAINING_POINTS,
                        GLOBALS.TRAINING_SET_METHOD,
                    )  # GLOBALS.TRAINING_POINTS contains the number of initial training points
                    # run the make_sets function on a compute node, which makes the training and sample pool sets from the points_location
                    job_id = IterStep(
                        submit_make_sets_job_to_auto_run,
                        IterUsage.All,
                        [points_location],
                    ).run(job_id, iter_state)
                    print(
                        f"Submitted: {job_id}"
                    )  # GLOBALS.TRAINING_POINTS is used in make_sets to make training sets with initial number of points
            else:
                IterArgs.nPoints.value = GLOBALS.POINTS_PER_ITERATION

            print(f"Submitting Iter: {i+1}")
            # initially job_id is none, then next_iter returns the job id of the submitted job. The next job has to wait for the previous job that was submitted.
            job_id = submit_auto_run_iter(func_order, job_id, iter_state)

            if MACHINE.submit_type.submit_after_final_step:
                break  # Only submit the first iteration for drop-n-compute and submit on compute
    return job_id


# used for Drop-n-compute
def submit_next_iter(current_iteration) -> Optional[JobID]:
    from ichor.globals import GLOBALS

    if MACHINE.submit_type is SubmitType.DropCompute:
        SCRIPT_NAMES.parent.value = DROP_COMPUTE_LOCATION

    iter_state = (
        IterState.Last
        if current_iteration == GLOBALS.N_ITERATIONS
        else IterState.Standard
    )

    with DataLock():
        return submit_auto_run_iter(get_func_order(), None, iter_state)


def rerun_from_failed() -> Optional[JobID]:
    from ichor.globals import GLOBALS

    current_iteration, max_iteration = read_counter(must_exist=False)

    if current_iteration < max_iteration and len(get_current_jobs()) == 0:
        GLOBALS.N_ITERATIONS = max_iteration - current_iteration
        GLOBALS.save_to_config()
        remove(FILE_STRUCTURE["counter"])
        return auto_run()


def auto_run_qct(directory: Path):
    qct_func_order = [
        *get_qcp_steps(),
        *get_qct_steps(),
    ]
    points = PointsDirectory(directory)
    IterArgs.nPoints.value = len(points)
    IterArgs.TrainingSetLocation = directory
    IterArgs.Atoms.value = points[0].atoms.names

    submit_auto_run_iter(qct_func_order)


def auto_make_models(
    directory: Path,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> JobID:
    func_order = [
        *get_model_steps(),
    ]

    IterArgs.TrainingSetLocation = directory
    if atoms is None:
        atoms = PointsDirectory(directory)[0].atoms.names
    IterArgs.Atoms.value = atoms
    if types is None:
        from ichor.main.make_models import default_model_type

        types = [default_model_type]
    IterArgs.ModelTypes.value = types
    return submit_auto_run_iter(func_order, wait_for_job=hold)
