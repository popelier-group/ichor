from typing import List

import numpy as np

from ichor.ichor_lib.atoms import ListOfAtoms
from ichor.make_sets.make_set_method import MakeSetMethod


class MinMax(MakeSetMethod):
    @classmethod
    def name(cls) -> str:
        return "min_max"

    @classmethod
    def get_npoints(cls, npoints: int, points: ListOfAtoms) -> int:
        return 2 * points[0].features.shape[-1]

    def get_points(self, points: ListOfAtoms) -> List[int]:
        from ichor.ichor_hpc.globals import GLOBALS

        atom = (
            GLOBALS.OPTIMISE_ATOM
            if GLOBALS.OPTIMISE_ATOM != "all"
            else GLOBALS.ATOMS[0].name
        )
        features = points[atom].features

        if features.ndim > 2:
            features = features[0]
        elif features.ndim < 2:
            features = features[:, np.newaxis]

        return list(np.argmin(features, axis=0)) + list(
            np.argmax(features, axis=0)
        )
