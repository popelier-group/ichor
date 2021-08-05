from pathlib import Path
from typing import Optional

from ichor.adaptive_sampling import AdaptiveSamplingMethod
from ichor.logging import logger
from ichor.models import Models
from ichor.points import PointsDirectory


def adaptive_sampling(
    model_directory: Optional[Path] = None,
    sample_pool_directory: Optional[Path] = None,
):
    from ichor.globals import GLOBALS

    if model_directory is None:
        model_directory = GLOBALS.FILE_STRUCTURE["models"]

    if sample_pool_directory is None:
        sample_pool_directory = GLOBALS.FILE_STRUCTURE["sample_pool"]

    models = Models(model_directory)
    sample_pool = PointsDirectory(sample_pool_directory)

    if GLOBALS.OPTIMISE_ATOM != "all":
        models = models[GLOBALS.OPTIMISE_ATOM]
        sample_pool = sample_pool[GLOBALS.OPTIMISE_ATOM]

    if GLOBALS.OPTIMISE_PROPERTY != "all":
        models = models[GLOBALS.OPTIMISE_PROPERTY]

    asm = AdaptiveSamplingMethod(models)
    points_to_add = asm(sample_pool, GLOBALS.POINTS_PER_ITERATION)

    for point in points_to_add:
        training_set = PointsDirectory(GLOBALS.FILE_STRUCTURE["training_set"])
        new_directory = (
            training_set.path
            / f"{GLOBALS.SYSTEM_NAME}{str(len(training_set)+1).zfill(4)}"
        )
        new_training_point = sample_pool[point]
        logger.info(
            f"Moved point {new_training_point.path} -> {new_directory}"
        )
        new_training_point.move(new_directory)
