from typing import List

import numpy as np

from ichor.atoms import ListOfAtoms
from ichor.make_sets.make_set_method import MakeSetMethod


class MinMaxMean(MakeSetMethod):
    @classmethod
    def name(cls) -> str:
        return "min_max_mean"

    @classmethod
    def get_npoints(cls, npoints: int, points: ListOfAtoms) -> int:
        return 3 * len(points[0].features)

    def get_points(self, points: ListOfAtoms) -> List[int]:
        from ichor.globals import GLOBALS

        atom = (
            GLOBALS.OPTIMISE_ATOM
            if GLOBALS.OPTIMISE_ATOM
            is not "all"  # matt_todo: this should be !=
            else GLOBALS.ATOMS[0].name
        )
        features = points[atom].features

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
