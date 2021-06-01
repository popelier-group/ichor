from typing import List

import numpy as np

from ichor.atoms import ListOfAtoms
from ichor.make_sets.make_set_method import MakeSetMethod


class MinMax(MakeSetMethod):
    @classmethod
    def name(cls) -> str:
        return "min_max"

    def get_points(self, points: ListOfAtoms) -> List[int]:
        features = points.features
        if features.ndim > 2:
            features = features[0]
        elif features.ndim < 2:
            features = features[:, np.newaxis]

        return list(np.argmin(features, axis=0)) + list(
            np.argmax(features, axis=0)
        )
