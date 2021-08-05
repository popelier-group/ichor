import numpy as np

from ichor.models.kernels.distance import Distance
from ichor.models.kernels.kernel import Kernel


class PeriodicKernel(Kernel):
    """Implemtation of the Periodic Kernel."""

    def __init__(self, lengthscale: np.ndarray, period: np.ndarray):
        """

        Args:
            :param: `lengthscale` np.ndarray of n_features:
                array of lengthscales
            :param: `period` np.ndarray of n_features:
                array of period lengths

        .. note::
            Lengthscales is typically n_features long because we want a separate lengthscale for each dimension.
            The periodic kernel is going to be used for phi features because these are the features we know can be cyclic.
            The period of the phi angle is always :math:`2\pi`, however this period can change if there is normalization
            or standardization applied to features. The new period then becomes the distance between where :math:`\pi` and :math:`-\pi`
            land after the features are scaled. Because the period can vary for individual phi angles for standardization, it is
            still passed in as an array that is n_features long.
        """

        self._lengthscale = lengthscale
        self._period = period

    @property
    def params(self):
        return self._lengthscale, self._period

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calcualtes Peridic covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The periodic covariance matrix of shape (n, m)
        """

        # TODO: lengthscales vs thetas. Using lengthscales simplifies the code here because you can divide inputs prior to computing distance matrix
        # TODO: using thetas which are 0.5*l^-2 then means you cannot just multiply by -theta here because they already include l^-2 instead of l^-1

        dist = Distance.euclidean_distance(x1, x2)
        dist *= np.pi
        dist /= self._period
        dist = 2 * np.power(np.sin(dist), 2)
        dist /= np.power(self._lengthscale, 2)

        return np.exp(dist)

    def r(self, x_test: np.ndarray, x_train: np.ndarray) -> np.ndarray:
        """helper method to return x_test, x_train Periodic covariance matrix K(X*, X)"""

        return self.k(x_test, x_train)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """helper method to return symmetric square matrix x_train, x_train Periodic covariance matrix K(X, X)"""

        return self.k(x_train, x_train)
