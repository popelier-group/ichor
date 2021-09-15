from pathlib import Path
from typing import Optional

from ichor.common.io import mkdir, remove
from ichor.logging import logger
from ichor.models import Models
from ichor.points import PointsDirectory


# todo: Maybe rename this function and file because it performs a bit more that just adaptive sampling.
def active_learning(
    model_directory: Optional[Path] = None,
    sample_pool_directory: Optional[Path] = None,
):
    """Add a new training point to the training set based on the most recent FERBUS model that was made. Adaptive sampling is
    used to add the worst performing point from the sample pool to the training set."""
    from ichor.active_learning import ActiveLearningMethod
    from ichor.auto_run import AutoRunOnly, submit_next_iter
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS
    from ichor.machine import MACHINE, SubmitType
    from ichor.arguments import Arguments

    if model_directory is None:
        model_directory = FILE_STRUCTURE["models"]

    if sample_pool_directory is None:
        sample_pool_directory = FILE_STRUCTURE["sample_pool"]

    current_iteration = 0
    if Arguments.auto_run:
        if FILE_STRUCTURE["counter"].exists():
            with open(FILE_STRUCTURE["counter"], "r") as f:
                current_iteration = int(f.read())

    models = Models(model_directory)
    sample_pool = PointsDirectory(sample_pool_directory)

    if GLOBALS.OPTIMISE_ATOM != "all":
        models = models[GLOBALS.OPTIMISE_ATOM]
        sample_pool = sample_pool[GLOBALS.OPTIMISE_ATOM]

    if GLOBALS.OPTIMISE_PROPERTY != "all":
        models = models[GLOBALS.OPTIMISE_PROPERTY]

    alm = ActiveLearningMethod(models)
    points_to_add = alm(sample_pool, GLOBALS.POINTS_PER_ITERATION)

    for point in points_to_add:
        training_set = PointsDirectory(FILE_STRUCTURE["training_set"])
        new_directory = (
            training_set.path
            / f"{GLOBALS.SYSTEM_NAME}{str(len(training_set)+1).zfill(4)}"
        )
        new_training_point = PointsDirectory(sample_pool_directory)[point]

        logger.info(
            f"Moved point {new_training_point.path} -> {new_directory}"
        )
        new_training_point.move(new_directory)

        if Arguments.auto_run:
            current_iteration += 1
            if not FILE_STRUCTURE["counter"].parent.exists():
                mkdir(FILE_STRUCTURE["counter"].parent)

            with open(FILE_STRUCTURE["counter"], "w") as f:
                f.write(f"{current_iteration}")

            if current_iteration == GLOBALS.N_ITERATIONS:
                remove(
                    FILE_STRUCTURE["counter"]
                )  # delete counter at the end of the auto run

            if current_iteration <= GLOBALS.N_ITERATIONS:
                if MACHINE.submit_type is SubmitType.DropCompute:
                    submit_next_iter(current_iteration)
