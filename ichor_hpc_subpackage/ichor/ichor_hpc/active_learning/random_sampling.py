import numpy as np

from ichor.active_learning.active_learning_method import ActiveLearningMethod
from ichor.ichor_lib.atoms import ListOfAtoms
from ichor.ichor_lib.common.functools import classproperty
from ichor.ichor_lib.models import Models


# todo: rename RandomSampling to RandomQuery
class RandomSampling(ActiveLearningMethod):
    """Method that moves a random set of points from the sample pool to the training set. This can be useful to increase
    the training set size rapidly because no extra computations need to be done, as well as many points can be added to the
    training set at once.
    """

    def __init__(self, models: Models):
        super().__init__(models)

    @classproperty
    def name(self) -> str:
        return "random"

    def get_points(self, points: ListOfAtoms, npoints) -> np.ndarray:
        """Gets indices of random points in the sample pool and adds them to the training set.

        :param points: A ListOfAtoms instance from which to take points
        :param npoints: The number of points which to add to the training set
        :return: The indices of randomly selected points which should be added to the training set
        """
        arr = np.arange(len(points))
        np.random.shuffle(arr)
        return arr[:npoints]
