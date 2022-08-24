from typing import List

import numpy as np
from ichor.core.atoms import ListOfAtoms
from ichor.hpc.make_sets.make_set_method import MakeSetMethod


class MinMaxMean(MakeSetMethod):
    @classmethod
    def name(cls) -> str:
        return "min_max_mean"

    @staticmethod
    def get_points_indices(points: ListOfAtoms, *args, **kwargs) -> List[int]:
        from ichor.hpc import GLOBALS

        atom = (
            GLOBALS.OPTIMISE_ATOM
            if GLOBALS.OPTIMISE_ATOM != "all"
            else GLOBALS.ATOMS[0].name
        )
        features = points[atom].features()

        if features.ndim > 2:
            features = features[:, 0, :]
        elif features.ndim < 2:
            features = features[:, np.newaxis]

        return (
            list(np.argmin(features, axis=0))
            + list(np.argmax(features, axis=0))
            + list(
                np.argmin(np.abs(features - np.mean(features, axis=0)), axis=0)
            )
        )
