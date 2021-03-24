import numpy as np

from ichor.models.kernels.kernel import Kernel
from ichor.models.kernels.distance import Distance


class RBFKernel(Kernel):
    """Implemtation of Radial Basis Function (RBF) kernel
    When each dimension has a separate lengthscale, this is also called the RBF-ARD kernel
    """

    def __init__(self, lengthscale: np.ndarray):
        
        self._lengthscale = lengthscale

    @property
    def params(self):
        return self._lengthscale

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """ Calcualtes RBF covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The RBF covariance matrix matrix of shape (n, m)
        """

        # TODO: lengthscales vs thetas. Using lengthscales simplifies the code here because you can divide inputs prior to computing distance matrix
        # TODO: using thetas which are 0.5*l^-2 then means you cannot just multiply by -theta here because they already include l^-2 instead of l^-1 
        x1 = x1 / self._lengthscale
        x2 = x2 / self._lengthscale

        dist = Distance.squared_euclidean_distance(x1, x2)

        return np.exp(-0.5 * dist)

    def r(self, x_test: np.ndarray, x_train: np.ndarray) -> np.ndarray:
        """ helper method to return x_test, x_train RBF covariance matrix K(X*, X)"""

        return self.k(x_test, x_train)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """ helper method to return symmetric square matrix x_train, x_train RBF covariance matrix K(X, X)"""

        return self.k(x_train, x_train)
