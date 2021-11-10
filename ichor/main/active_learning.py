from pathlib import Path
from typing import Optional

from ichor.common.io import mkdir, remove
from ichor.files import PointsDirectory
from ichor.logging import logger
from ichor.models import Models
from ichor.auto_run.counter import read_counter, write_counter


def active_learning(
    model_directory: Optional[Path] = None,
    sample_pool_directory: Optional[Path] = None,
):
    """Add a new training point to the training set based on the most recent FERBUS model that was made. Adaptive sampling is
    used to add the worst performing point from the sample pool to the training set."""
    from ichor.active_learning import learning_method_cls
    from ichor.arguments import Arguments
    from ichor.auto_run.standard_auto_run import submit_next_iter
    from ichor.file_structure import FILE_STRUCTURE
    from ichor.globals import GLOBALS
    from ichor.machine import MACHINE
    from ichor.submission_script import SUBMIT_ON_COMPUTE

    if model_directory is None:
        model_directory = FILE_STRUCTURE["models"]

    if sample_pool_directory is None:
        sample_pool_directory = FILE_STRUCTURE["sample_pool"]

    current_iteration = 0
    max_iteration = GLOBALS.N_ITERATIONS
    if Arguments.auto_run and FILE_STRUCTURE["counter"].exists():
        current_iteration, max_iteration = read_counter()

    models = Models(model_directory)
    sample_pool = PointsDirectory(sample_pool_directory)

    if GLOBALS.OPTIMISE_ATOM != "all":
        models = models[GLOBALS.OPTIMISE_ATOM]
        sample_pool = sample_pool[GLOBALS.OPTIMISE_ATOM]

    if GLOBALS.OPTIMISE_PROPERTY != "all":
        models = models[GLOBALS.OPTIMISE_PROPERTY]

    # make the learning method instance given a set of models
    learning_method_inst = learning_method_cls(models)
    # use the __call__ method to calculate which points to add from the sample pool to the training set based on the given models
    points_to_add = learning_method_inst(
        sample_pool, GLOBALS.POINTS_PER_ITERATION
    )

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
            logger.info(f"Completed iteration {current_iteration} of {max_iteration}")

            current_iteration += 1
            write_counter(current_iteration, max_iteration)
            if current_iteration == max_iteration:
                remove(
                    FILE_STRUCTURE["counter"]
                )  # delete counter at the end of the auto run

            if (
                current_iteration <= max_iteration
                and MACHINE.submit_type.submit_after_final_step
            ):
                logger.info(f"Submitting iteration {current_iteration}")
                with SUBMIT_ON_COMPUTE:
                    submit_next_iter(current_iteration)
