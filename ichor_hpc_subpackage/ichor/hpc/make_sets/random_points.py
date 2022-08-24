import random
from typing import List
from ichor.hpc.make_sets.make_set_method import MakeSetMethod


class RandomPoints(MakeSetMethod):
    """Chooses random points from the sample pool which are added to the training set"""

    @classmethod
    def name(cls) -> str:
        return "random"

    @staticmethod
    def get_points_indices(points: "ListOfAtoms", npoints: int) -> List[int]:
        return random.sample(
            range(len(points)), k=min(npoints, len(points))
        )
