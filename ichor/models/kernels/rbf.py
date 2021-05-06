import numpy as np

from ichor.models.kernels.distance import Distance
from ichor.models.kernels.kernel import Kernel


class RBF(Kernel):
    """Implemtation of Radial Basis Function (RBF) kernel
    When each dimension has a separate lengthscale, this is also called the RBF-ARD kernel
    """

    def __init__(self, lengthscale: np.ndarray):

        self._lengthscale = 1.0/lengthscale

    @property
    def params(self):
        return self._lengthscale

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calcualtes RBF covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The RBF covariance matrix of shape (n, m)
        """

        # TODO: lengthscales vs thetas. Using lengthscales simplifies the code here because you can divide inputs prior to computing distance matrix
        # TODO: using thetas which are 0.5*l^-2 then means you cannot just multiply by -theta here because they already include l^-2 instead of l^-1
        x1 = x1 * self._lengthscale
        x2 = x2 * self._lengthscale

        dist = Distance.squared_euclidean_distance(x1, x2)
        return np.exp(-0.5 * dist)

        # dist = np.empty((x1.shape[0], x2.shape[0], x1.shape[1]))
        # for i, xi in enumerate(x1):
        #     for j, xj in enumerate(x2):
        #         diff = xi - xj
        #         dist[i, j, :] = diff * diff
        #
        # return np.exp(-0.5 * np.sum(dist / self._lengthscale, axis=2))
