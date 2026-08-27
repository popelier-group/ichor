"""What the model analysis menu and its submenus both need.

The overfitting check lives in its own submenu of the model analysis menu, so the pieces
the two share (where analysis output goes, how model folders are found, and how the
overfitting jobs are submitted) live here rather than in either of them: the menu imports
the submenu in order to attach it, so anything the submenu took from the menu directly
would be a circular import.
"""

from pathlib import Path
from typing import List, Optional, Tuple

import ichor.cli.global_menu_variables
from ichor.cli.useful_functions import (
    batch_system_available,
    directory_selected,
    job_memory_gb,
    user_input_free_flow,
)
from ichor.core.models import Model, Models
from ichor.hpc.main import submit_overfitting_report
from tqdm import tqdm

# held-out split naming used in FEREBUS/ichor training CSV file names
EXTERNAL_SET_TYPE = "EXT_VALIDATION_SET"
INTERNAL_SET_TYPE = "INT_VALIDATION_SET"

# analysis outputs (S-curves, plots, metrics) are written into this subfolder of
# the model folder, to keep each model batch's results tidy
ANALYSIS_SUBFOLDER = "analysis"

# output file names (fixed; identity comes from the analysis/ folder location)
S_CURVES_EXCEL_NAME = "s-curves.xlsx"
S_CURVES_PLOT_NAME = "s-curves.png"
S_CURVES_CSV_NAME = "s-curves.csv"
METRICS_CSV_NAME = "model_metrics.csv"
OVERFITTING_CSV_NAME = "overfitting_report.csv"

# which option selects the models the analysis is run on, so that an option which is
# picked before it has been used says what to do about it
SELECT_MODELS_WITH = "Use 'Select models directory' in the Model Analysis Menu first."

# The share of the job's memory the worker estimate is allowed to fill. The rest covers
# what is not worth modelling: the interpreter and its imports in each worker, the
# held-out data they are given, and however much the batch system counts on top of what
# python asks for.
MEMORY_FRACTION = 0.7


def pause(message: str = ""):
    """Shows ``message`` (if any) and then waits for the user to press enter. The
    "Press enter to continue" prompt is always put on its own line so it is clear
    that user interaction is needed."""
    if message:
        print(message)
    user_input_free_flow("Press enter to continue: ")


def selected_models_path() -> Path:
    """The models directory the model analysis menu is pointed at."""

    return Path(ichor.cli.global_menu_variables.SELECTED_MODELS_PATH)


def selected_set_type() -> str:
    """The held-out split the model analysis menu is set to."""

    return ichor.cli.global_menu_variables.SELECTED_MODEL_SET_TYPE


def models_directory_selected(action: str, holds_models: bool = True) -> bool:
    """Checks that the models directory an option is about to be run on has been
    selected, and tells the user what to select if it has not.

    The models path starts out as the directory ichor is running in, so an option which
    is picked before it has been selected is handed the working directory: the analysis
    of it then finds no models (or, for the options which search a whole tree of model
    folders, walks everything below wherever ichor was started) rather than saying that
    nothing was selected.

    :param action: What the option would do with the models, e.g. ``"make the
        S-curves"``.
    :param holds_models: Whether the directory has to hold the ``.model`` files itself,
        defaults to True. Pass False for the options which are pointed at a parent of
        model folders (e.g. ``6_MODELS``), which holds no models of its own.
    :return: True if the option can go ahead, False if it cannot (in which case the user
        has been shown what is wrong).
    """

    return directory_selected(
        selected_models_path(),
        action,
        what="models directory",
        holds="*.model" if holds_models else None,
        holds_description="models (.model files)",
        select_with=SELECT_MODELS_WITH,
    )


def analysis_output_path(base_name: str, models_path: Optional[Path] = None) -> Path:
    """Builds the full path for an analysis output file, placed inside an
    ``analysis`` subfolder of the model folder (created if needed), e.g.::

        <models_path>/analysis/s-curves.xlsx

    Writing outputs into each model's own ``analysis`` folder (rather than the
    current directory) keeps each model batch's results tidy and self-identifying
    by their location, so no filename prefix is needed.

    :param base_name: The base output file name, e.g. ``s-curves.xlsx``.
    :param models_path: The model folder to write into. Defaults to the currently
        selected models path.
    """

    if models_path is None:
        models_path = selected_models_path()
    models_path = Path(models_path)

    analysis_dir = models_path / ANALYSIS_SUBFOLDER
    analysis_dir.mkdir(parents=True, exist_ok=True)

    return analysis_dir / base_name


def discover_model_folders(root: Path) -> List[Path]:
    """Finds model folders (directories that directly contain ``.model`` files)
    under ``root``. If ``root`` is itself a model folder it is returned on its own.
    Used to run analysis over a whole parent folder of model batches, e.g. every
    ``SEQ-XX-YY-ZZ`` folder under ``6_MODELS`` (the layout produced by the extract
    step)."""

    root = Path(root)
    if not root.is_dir():
        return []
    if Models.check_path(root):
        return [root]
    return sorted(
        d
        for d in tqdm(root.rglob("*"), desc="Scanning for model folders")
        if d.is_dir() and Models.check_path(d)
    )


def models_in_largest_batch(model_folders: List[Path]) -> int:
    """Returns how many models the biggest of the given batches holds.

    One overfitting job is submitted per batch and they all ask for the same number of
    cores, so it is the biggest batch that says how many cores can be put to use. The
    batches under a system folder are the different training set sizes of the same
    system, so in the usual case they all hold the same models anyway.

    :param model_folders: The model folders (batches) that are to be checked.
    :return: The number of ``.model`` files in the one holding the most, or 0 when
        there are no batches.
    """

    return max(
        (len(list(folder.glob("*.model"))) for folder in model_folders),
        default=0,
    )


def overfitting_worker_memory_gb(ntrain: int, n_features: int) -> float:
    """Estimates the memory one model check needs at its peak, in GB.

    Checking a model is dominated not by the covariance matrix itself but by the arrays
    built on the way to it. ``RBFCyclic.k`` subtracts every training point from every
    other one feature by feature, which is an ``(ntrain, ntrain, n_features)`` array,
    and the cyclic correction of the phi features (every third one) copies that array's
    masked columns a couple of times over. The covariance matrix, its inverse and the
    two intermediates of the kernel are each a further ``ntrain`` by ``ntrain``.

    Measured against the real arrays this comes out within a few percent for training
    sets from 500 to 1500 points.

    :param ntrain: The number of training points of the model.
    :param n_features: The number of features of the model, i.e. 3N-6 for an N atom
        system.
    :return: The estimate in GB, or 0.0 when the dimensions are not known.
    """

    if ntrain <= 0 or n_features <= 0:
        return 0.0

    # the phi features, which are every third one, are copied twice by the correction
    cyclic_features = 2 * -(-n_features // 3)
    # R, its inverse, and the two intermediates the kernel builds on the way to it
    matrices = 4

    doubles = ntrain * ntrain * (n_features + cyclic_features + matrices)

    return doubles * 8 / 1e9


def largest_training_set(model_folders: List[Path]) -> Tuple[int, int]:
    """Returns the dimensions of the biggest training set among the given batches.

    One model is read per batch rather than all of them, as every model of a batch is
    trained on the same set of points and so has the same dimensions. The biggest is
    what the memory estimate has to be made for, as one number of cores is used for
    every batch.

    :param model_folders: The model folders (batches) that are to be checked.
    :return: (training points, features) of the biggest, or (0, 0) if nothing could be
        read.
    """

    ntrain, n_features = 0, 0

    for folder in model_folders:
        model_files = sorted(folder.glob("*.model"))
        if not model_files:
            continue

        try:
            model = Model(model_files[0])
            batch_ntrain, batch_features = int(model.ntrain), int(model.x.shape[1])
        # a model file which cannot be read is reported by the check itself; here it
        # only means this batch cannot be measured
        except Exception:  # noqa: BLE001
            continue

        if batch_ntrain > ntrain:
            ntrain, n_features = batch_ntrain, batch_features

    return ntrain, n_features


def workers_that_fit(ncores: int, worker_memory_gb: float) -> int:
    """Returns how many models a job of ``ncores`` cores can check at once without
    running out of memory.

    The batch system hands out memory per core, so a job of ``ncores`` cores has
    ``ncores`` times one core's memory to share between its workers. One worker per core
    is what makes the check fastest, but a worker of a large training set can need more
    than the one core's worth that would give it, in which case the job still asks for
    the cores (that is how it is given the memory) and simply runs fewer workers.

    :param ncores: The number of cores the job asks for.
    :param worker_memory_gb: What one worker needs, from
        :func:`overfitting_worker_memory_gb`. 0 when it is not known, in which case one
        worker per core is assumed.
    :return: The number of workers, at least 1 and never more than ``ncores``.
    """

    if worker_memory_gb <= 0.0:
        return max(1, ncores)

    affordable = int(MEMORY_FRACTION * job_memory_gb(ncores) / worker_memory_gb)

    return max(1, min(ncores, affordable))


def submit_overfitting_for_folders(
    model_folders: List[Path], ncores: int, workers: Optional[int] = None
) -> Tuple[List[Path], List[Path]]:
    """Submits one overfitting-check job per model folder.

    Each folder's report is written into its own ``analysis`` subfolder, next to the
    S-curves and metrics of the same batch, so a queued check ends up in the same place
    as the analysis it belongs with.

    :param model_folders: The model folders to check, one job each.
    :param ncores: Number of cores each job asks for.
    :param workers: Number of models each job checks at once. Defaults to one per core,
        which is the fastest; fewer are used when a worker needs more memory than one
        core brings (see :func:`workers_that_fit`).
    :return: (the folders whose job was submitted, the folders whose job was not).
    """

    set_type = selected_set_type()
    submitted, failed = [], []

    for model_folder in model_folders:
        # the report goes next to the rest of that batch's analysis
        output_path = analysis_output_path(OVERFITTING_CSV_NAME, model_folder)

        # a batch with no held-out CSVs is still worth checking: the leave-one-out half
        # of the report needs nothing but the models themselves
        csv_files = sorted(model_folder.rglob(f"*_{set_type}.csv"))
        split_for_job = set_type if csv_files else ""

        try:
            job_id = submit_overfitting_report(
                model_folder,
                output_path,
                set_type=split_for_job,
                ncores=ncores,
                workers=workers,
            )
        # a job which cannot be submitted should not stop the rest from being, and
        # should not take the menu down with it either
        except Exception as error:  # noqa: BLE001 - reported to the user below
            print(f"Could not submit the overfitting check of {model_folder}: {error}")
            failed.append(model_folder)
            continue

        if job_id is None:
            failed.append(model_folder)
        else:
            submitted.append(model_folder)

    return submitted, failed


def overfitting_submission_notes(ncores: int, workers: int) -> List[str]:
    """The sentences describing what a set of submitted overfitting jobs will do, shared
    by the summaries of the options which submit them.

    :param ncores: The cores each job asks for.
    :param workers: The models each job checks at once.
    """

    return [
        "The overfitting check was NOT run here: it has been submitted to the batch "
        "system as one queued job per model folder, because it takes far longer than "
        "the rest of the analysis.",
        f"Each of those jobs checks {workers} model(s) at once and writes its report "
        f"to {ANALYSIS_SUBFOLDER}/{OVERFITTING_CSV_NAME} inside its own model folder, "
        "next to the S-curves and metrics of the same batch. Those report files do "
        "not exist yet, and will not until the jobs have run.",
        *(
            [
                f"Fewer models are checked at once ({workers}) than the {ncores} cores "
                "asked for, because one check of a training set this size needs more "
                "memory than one core brings. The cores are still what the job is "
                "given that memory by."
            ]
            if workers < ncores
            else []
        ),
        "The jobs are queued, so they will not start immediately and this menu does "
        "not wait for them. Check on them with your batch system's queue command "
        "(e.g. qstat / squeue).",
    ]


def no_batch_system_note() -> str:
    """What to tell the user when there is no queue to submit the overfitting check to."""

    return (
        "No batch system (SGE or SLURM) was found on this machine, so there is no "
        "queue to submit the overfitting check to. Run it from the Overfitting Check "
        "Menu instead, which checks the models here and now."
    )


def batch_system_is_set_up() -> bool:
    """Whether the overfitting check can be queued rather than run here."""

    return batch_system_available()
