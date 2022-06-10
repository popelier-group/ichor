from typing import List

import numpy as np
from ichor.cli.make_set_methods.make_set_method import MakeSetMethod
from ichor.core.atoms import ListOfAtoms


class MinMaxMean(MakeSetMethod):
    @classmethod
    def name(cls) -> str:
        return "min_max_mean"

    @classmethod
    def get_npoints(cls, npoints: int, points: ListOfAtoms) -> int:
        return 3 * points[0].features.shape[-1]

    def get_points(self, points: ListOfAtoms) -> List[int]:
        from ichor.hpc import GLOBALS

        atom = (
            GLOBALS.OPTIMISE_ATOM
            if GLOBALS.OPTIMISE_ATOM != "all"
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
