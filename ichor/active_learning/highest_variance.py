import json
from typing import Dict

import numpy as np
import numpy.linalg as la
from scipy.spatial.distance import cdist

from ichor.active_learning.active_learning_method import ActiveLearningMethod
from ichor.atoms import ListOfAtoms
from ichor.common.functools import classproperty
from ichor.common.io import mkdir
from ichor.models import ModelsResult, Models

class HighestVariance(ActiveLearningMethod):
    """ Active learning method which calculates the variance of the sample pool points (given the models) and adds
    points with the highest variance to the training set.
    
    .. note::
        Only one point, the one with the highest variance in the sample pool, is added by default.
    """

    def __init__(self, models: Models):
        ActiveLearningMethod.__init__(self, models)

    @classproperty
    def name(self) -> str:
        return "highest_variance"

    def get_points(self, points: ListOfAtoms, npoints: int) -> np.ndarray:

        features_dict = self.models.get_features_dict(points)
        variance = self.models.variance(features_dict)

        from ichor.file_structure import FILE_STRUCTURE

        cv_file = FILE_STRUCTURE["highest_variance"]
        mkdir(cv_file.parent)
        if cv_file.exists():
            cv_file.unlink()  # delete previous cv_errors to prevent bug where extra closing brackets were present
        with open(
            cv_file, "w"
        ) as f:  # store data as json for next iterations alpha calculation
            json.dump(
                {
                    "added_points": npoints,
                    "cv_errors": cv_errors[epe].to_list(),
                    "predictions": self.models.predict(features_dict)[
                        epe
                    ].to_list(),
                },
                f,
            )

        return epe
