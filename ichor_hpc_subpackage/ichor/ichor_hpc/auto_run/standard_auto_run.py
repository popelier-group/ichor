""" Standard auto run implementation which runs iteration containing Gaussian, FEREBUS, jobs"""


from enum import Enum
from pathlib import Path
from time import sleep
from typing import Any, Callable, List, Optional, Sequence, Tuple

from ichor.auto_run.auto_run_aimall import submit_aimall_job_to_auto_run
from ichor.auto_run.auto_run_ferebus import submit_ferebus_job_to_auto_run
from ichor.auto_run.auto_run_gaussian import submit_gaussian_job_to_auto_run
from ichor.auto_run.auto_run_morfi import submit_morfi_job_to_auto_run
from ichor.auto_run.auto_run_pyscf import submit_pyscf_job_to_auto_run
from ichor.auto_run.counter import (counter_exists, get_counter_location,
                                    read_counter, write_counter)
from ichor.auto_run.ichor_jobs import (
    make_models, submit_ichor_active_learning_job_to_auto_run,
    submit_ichor_aimall_command_to_auto_run,
    submit_ichor_gaussian_command_to_auto_run,
    submit_ichor_morfi_command_to_auto_run,
    submit_ichor_pyscf_command_to_auto_run, submit_make_sets_job_to_auto_run)
from ichor.auto_run.stop import start
from ichor.ichor_hpc.batch_system import BATCH_SYSTEM, JobID, NodeType
from ichor.ichor_lib.common.bool import check_bool
from ichor.ichor_lib.common.int import truncate
from ichor.ichor_lib.common.io import mkdir, move, remove
from ichor.ichor_lib.common.points import get_points_location
from ichor.ichor_lib.common.types import MutableValue
from ichor.ichor_hpc.drop_compute.drop_compute import (DROP_COMPUTE_LOCATION, DROP_COMPUTE_MAX_JOBS,
                                DROP_COMPUTE_NTRIES, DROP_COMPUTE_TMP_LOCATION)
from ichor.ichor_hpc import FILE_STRUCTURE
from ichor.ichor_lib.files import PointsDirectory, Trajectory
from ichor.ichor_hpc.batch_system.machine_setup import MACHINE, SubmitType
from ichor.main.queue import get_current_jobs
from ichor.make_sets import make_sets_npoints
from ichor.qcp import QUANTUM_CHEMISTRY_PROGRAM, QuantumChemistryProgram
from ichor.qct import (QUANTUM_CHEMICAL_TOPOLOGY_PROGRAM,
                       QuantumChemicalTopologyProgram)
from ichor.submission_script import SCRIPT_NAMES, DataLock


class AutoRunAlreadyRunning(Exception):
    pass


class DropComputeSubmitFailed(Exception):
    pass


class IterState(Enum):
    """The iteration which the adaptive sampling is on. There could be extra (or less) programs that need to be ran depending on
    which iteration the ICHOR auto run is on. For example, in the standard auto run, the First step is making the training, validation, sample sets.
    The Standard iterations are ones that occur between the First and Last iteration. For the Standard iterations, we need to run
    Gaussian, AIMALL, FEREBUS, and adaptive sampling to add next point. For The Last iteration, we do NOT want to run the adaptive sampling, as that
    will a new point to the training set for which Gaussian AIMALL, FEREBUS are not going to be ran."""

    First = 1
    Standard = 2
    Last = 3


class IterUsage(Enum):
    """Tells the IterStep whether or not this step of the auto run should be ran, given the IterState of the current auto run iteration.
    For example, IterUsage for the IterStep which runs the ICHOR adaptive sampling will be set to IterUsage.AllButLast, which means that the
    adaptive sampling step will not be ran as the last step of the last auto run iteration because we do not want to add a new point on the very
    last auto run iteration (as Gaussian/AIMALL will not be ran on that newly added point)."""

    First = 0
    All = 1
    AllButLast = 2

    def __contains__(self, state: IterState):
        return self is not IterUsage.AllButLast or state is not IterState.Last


class IterArgs:
    """An Enum containing various arguments that could be needed by the various steps in one of the adaptive sampling iterations. Note that
    the elements do not have constant values, as we need to be able to change the training set locations, number of points, etc. depending on
    where we are doing the adaptive sampling (for example when doing per-atom adaptive sampling)."""

    TrainingSetLocation = MutableValue(FILE_STRUCTURE["training_set"])
    SamplePoolLocation = MutableValue(FILE_STRUCTURE["sample_pool"])
    FerebusDirectory = MutableValue(FILE_STRUCTURE["ferebus"])
    ModelLocation = MutableValue(FILE_STRUCTURE["models"])
    nPoints = MutableValue(1)  # Overwritten Based On IterState
    Atoms = MutableValue([])  # Overwritten from GLOBALS.ATOMS
    ModelTypes = MutableValue([])
    Force = MutableValue(False)


class IterStep:
    """A class which wraps around ONE step of ONE active learning iteration
    (each Standard iteration has Gaussian, AIMALL, FEREBUS, and ICHOR adaptive sampling steps).

    :param func: A `submit` function which submits one type of job (eg. Gaussian or AIMALL job)
    :param usage: An IterUsage element
    :param args: Any arguments that need to be passed to the submit function, such as Training Set Locations, Sample Set Locations, Etc.
    """

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
        """Runs the submit function, which submits the specified job to the queueing system on the machine. If this job needs to wait for a previous
        job to finish (as it needs the outputs of the previous job), then a `wait_for_job` argument is passed as well, which is of type `JobID`

        :param wait_for_job: A `JobID` instance, which contains job-related information, such as the job id. This is to hold the current job for the
            previous job to finish.
        :param state: An `IterState` instance
        :return: A `JobID` instance which wraps around the current job id that was submitted.
        """
        if state in self.usage:
            return self.func(*self.args, hold=wait_for_job)
        else:
            return wait_for_job


def submit_auto_run_iter(
    func_order: List[IterStep],
    wait_for_job: Optional[JobID] = None,
    state: IterState = IterState.Standard,
) -> Optional[JobID]:
    """Submits all jobs required for one auto run iteration. Thus, this function submits Gaussian, AIMALL, FEREBUS, adaptive sampling jobs.
    Additionally, the first and last jobs have different programs being ran. The first job of the first iteration needs to be make sets, where
    the initial training set, validation set, sample pool sets are made. The final job of the final iteration is FEREBUS (NOT Adaptive sampling), as
    we do NOT want to add a new point in the last iteration, because then we will have a new point for which Gaussian, AIMALL, etc. have not been ran.

    :param func_order: A List of `IterStep` which contains all the `submit`-type functions that submit the different kinds of jobs. The order of this list
        matters because this is how we need to run programs, eg. AIMALL cannot be ran before Gaussian has ran for a point (so it has to hold queue wait for
        Gaussian to finish)/
    :param wait_for_job: An Optional `JobID` argument that can be passed which tells the first job of the iteration to wait for a previously submitted job.
    :param state: An `IterState`, which tells what type of iteration we are on. Most of the iterations are IterState.Standard, where all programs are executed.
        But can also be IterState.Last for the Last iteration of the auto run.
    """

    from ichor.ichor_hpc.globals import GLOBALS

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
        # Other jobs will be IterState.Standard (apart from IterState.Last), thus we run the sequence of jobs specified in func_order
        for i, iter_step in enumerate(func_order):
            # append the modified id to the submission script name as this is how drop-in-compute holds jobs
            if (
                MACHINE.submit_type is SubmitType.DropCompute
                and BATCH_SYSTEM.current_node() is NodeType.ComputeNode
            ):
                modify = f"+{modify_id}"
                if i > 0:
                    modify += f"+hold_{modify_id - 1}"  # hold for the previous job (whose job id is one less than this job)
                SCRIPT_NAMES.modify.value = modify
                modify_id += 1
            job_id = iter_step.run(job_id, state)
            if job_id is not None:
                print(f"Submitted: {job_id}")

    # always return the job_id at the end because we need to hold next jobs
    return job_id


def get_qcp_steps() -> Tuple[IterStep, IterStep]:  # Gaussian / PySCF
    """Get the quantum chemistry program (QCP) which is going to be used to generate .wfn files. This can either be Gaussian or PySCF. This program used determines which
    `submit` functions are going to be used (either submit_gaussian_job_to_auto_run or submit_pyscf_job_to_auto_run).

    :return: A tuple of two IterStep. The first IterStep is an ICHOR job, which sets up datafiles needed for a Gaussian/PySCF job.
        The second step is the actual Gaussian/PySCF job where a .wfn file is produced.
    """
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
        [IterArgs.TrainingSetLocation, IterArgs.Force],
    )
    qcp_step = IterStep(qcp_function, IterUsage.All, [IterArgs.nPoints])

    return ichor_qcp_step, qcp_step


def get_qct_steps() -> Tuple[IterStep, IterStep]:  # AIMAll / Morfi
    """Get the quantum chemistry topology (QCT) This can either be AIMALL or Morfi. This program used determines which
    `submit` functions are going to be used (either submit_gaussian_job_to_auto_run or submit_pyscf_job_to_auto_run).

    :return: A tuple of two IterStep. The first IterStep is an ICHOR job, which sets up datafiles needed for an AIMALL/Morfi job.
        The second step is the actual AIMALL/Morfi job.
    """
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
        [IterArgs.TrainingSetLocation, IterArgs.Atoms, IterArgs.Force],
    )

    qct_step = IterStep(
        qct_function,
        IterUsage.All,
        [IterArgs.nPoints, IterArgs.Atoms],
    )

    return ichor_qct_step, qct_step


def get_model_steps() -> Tuple[IterStep, IterStep]:
    """Get the functions which are going to submit machine learning-related jobs to the queueing system.

    :return: A tuple of IterStep. The first IterStep is an ICHOR job which writes out FEREBUS configuration settings.
        The second job is the actual FEREBUS job when GPR models are made.
    """
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


def get_func_order() -> List[IterStep]:
    """Returns a list of IterSteps which tell the auto run the sequence in which jobs are to be ran (eg. ICHOR job writes out Gaussian files,
    Gaussian can then run, then ICHOR job writes out AIMALL-related files, the AIMALL runs, then ICHOR writes out FEREBUS-related files, then
    FEREBUS runs, finally, ICHOR adds a new point to the training set using adaptive sampling). These steps must be ran in the correct order as the
    output of one step is a required input to the next step.

    :return: A list of IterStep. Each IterStep contains a `submit` function which submits a different type of job (ICHOR, Gaussian, AIMALL, etc.). Note
        that IterUsage tells IterStep if the particular jobs needs to be submitted, depending on the auto-run iteration. For example, the last
        auto run iteration we do NOT need to run `submit_ichor_active_learning_job_to_auto_run` as we do NOT want a new point to be added on the very
        last active learning iteration. Thus this IterStep which wraps around `submit_ichor_active_learning_job_to_auto_run` has `IterUsage.AllButLast`.
    """
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


def setup_iter_args():
    """Sets up the IterArgs Enum values. Even though `IterArtgs` is an Enum, the values associated with the elements are type `MutableValue` because
    they need to be able to change values (because the GLOBALS values can change)."""
    from ichor.ichor_hpc.globals import GLOBALS

    if GLOBALS.OPTIMISE_ATOM == "all":
        IterArgs.Atoms.value = [atom.name for atom in GLOBALS.ATOMS]
    else:
        IterArgs.Atoms.value = [GLOBALS.OPTIMISE_ATOM]

    if GLOBALS.OPTIMISE_PROPERTY == "all":
        from ichor.main.make_models import MODEL_TYPES

        IterArgs.ModelTypes.value = MODEL_TYPES()
    else:
        types = GLOBALS.OPTIMISE_PROPERTY
        if isinstance(types, str):
            types = [types]
        IterArgs.ModelTypes.value = types


def check_auto_run_running(wrkdir: Optional[Path] = None) -> bool:
    """Checks whether a file named `counter` exists. This file keeps track of the auto run iteration that is currently being ran (it just contains a number
    to show which auto run iteration is currently running and the total number of iterations, as set by GLOBALS).
    This file is by default found at FILE_STRUCTURE["counter"].

    :return: Returns True if `counter` file exists or False if a `counter` file does not exist.
    """
    if wrkdir is None:
        wrkdir = Path.cwd()
    return counter_exists(wrkdir)


def auto_run_from_menu() -> JobID:
    """Function that interacts with ICHOR's menus. If a counter file exists, this function asks if the counter files should be deleted before
    starting auto run again. Finally, the `auto_run` function is ran, which submits the jobs to the queueing system."""

    if check_auto_run_running():
        counter_location = get_counter_location()
        current_iter, max_iter = read_counter(counter_location)
        print(f"Auto-run may already be running, '{counter_location}' exists.")
        print(
            f"Counter file suggests auto-run is on iteration {current_iter} out of {max_iter} iterations."
        )
        remove_counter = check_bool(
            input("Remove file: {counter_location}: [Y/N] ")
        )
        if remove_counter:
            remove(counter_location)
    return auto_run()


def auto_run() -> JobID:
    """Auto run Gaussian, AIMALL, FEREBUS, and ICHOR jobs needed to make GP models."""
    from ichor.ichor_hpc.globals import GLOBALS

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

    setup_iter_args()

    job_id = None
    with DataLock():
        start()
        for i, iter_state in enumerate(iterations):
            # the first job will execute this since the first iteration is IterState.First
            if iter_state is IterState.First:
                if IterArgs.TrainingSetLocation.value.exists():
                    IterArgs.nPoints.value = len(
                        PointsDirectory(IterArgs.TrainingSetLocation.value)
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
    """Submits next iteration of auto run for DropCompute. The last job id of the job sequence that was submitted is optionally returned."""

    from ichor.ichor_hpc.globals import GLOBALS

    if MACHINE.submit_type is SubmitType.DropCompute:
        SCRIPT_NAMES.parent.value = DROP_COMPUTE_TMP_LOCATION
        mkdir(SCRIPT_NAMES.parent.value)

    setup_iter_args()
    IterArgs.nPoints.value = GLOBALS.POINTS_PER_ITERATION

    iter_state = (
        IterState.Last
        if current_iteration == GLOBALS.N_ITERATIONS
        else IterState.Standard
    )

    with DataLock():
        final_job = submit_auto_run_iter(get_func_order(), None, iter_state)

    if MACHINE.submit_type is SubmitType.DropCompute:
        if not DROP_COMPUTE_LOCATION.exists():
            mkdir(DROP_COMPUTE_LOCATION)

        njobs_queued = sum(
            f.suffix.startswith(".sh")
            for f in DROP_COMPUTE_TMP_LOCATION.iterdir()
            if f.is_file()
        )

        for _ in range(DROP_COMPUTE_NTRIES):
            njobs_waiting = sum(
                f.suffix.startswith(".sh")
                for f in DROP_COMPUTE_LOCATION.iterdir()
                if f.is_file()
            )
            if njobs_waiting + njobs_queued > DROP_COMPUTE_MAX_JOBS:
                sleep(30)
            else:
                for script in DROP_COMPUTE_TMP_LOCATION.iterdir():
                    move(script, DROP_COMPUTE_LOCATION / script.name)
                remove(DROP_COMPUTE_TMP_LOCATION)
                break
        else:
            remove(DROP_COMPUTE_TMP_LOCATION)
            raise DropComputeSubmitFailed(
                f"Failed to submit to DropCompute too many times ({DROP_COMPUTE_NTRIES})"
            )

    return final_job


def rerun_from_failed() -> Optional[JobID]:
    from ichor.ichor_hpc.globals import GLOBALS

    current_iteration, max_iteration = read_counter(must_exist=False)

    if (
        FILE_STRUCTURE["counter"].exists()
        and current_iteration < max_iteration
        and len(get_current_jobs()) == 0
    ):
        GLOBALS.N_ITERATIONS = max_iteration - current_iteration
        GLOBALS.save_to_config()
        remove(FILE_STRUCTURE["counter"])
        return auto_run()


def auto_run_qct(directory: Path, force: bool = False):
    """Only submit QCP and QCT steps, Gaussian and AIMALL (or PySCF and Morfi), steps to auto run. Do not make GPR models."""
    qct_func_order = [
        *get_qcp_steps(),
        *get_qct_steps(),
    ]
    points = PointsDirectory(directory)
    IterArgs.nPoints.value = len(points)
    IterArgs.TrainingSetLocation.value = directory
    IterArgs.Atoms.value = points[0].atoms.names
    IterArgs.Force.value = force

    with DataLock():
        submit_auto_run_iter(qct_func_order)


def auto_make_models(
    directory: Path,
    atoms: Optional[List[str]] = None,
    types: Optional[List[str]] = None,
    hold: Optional[JobID] = None,
) -> JobID:
    """Only submit GPR-related jobs (such as FERREBUS jobs). Do not run Gaussian or AIMALL (or PySCF and Morfi).

    :return: a JobID instance which contains information about the last job that was submitted
    """
    func_order = [
        *get_model_steps(),
    ]

    IterArgs.TrainingSetLocation.value = directory
    if atoms is None:
        atoms = PointsDirectory(directory)[0].atoms.names
    IterArgs.Atoms.value = atoms
    if types is None:
        from ichor.main.make_models import default_model_type

        types = [default_model_type]
    IterArgs.ModelTypes.value = types
    return submit_auto_run_iter(func_order, wait_for_job=hold)
