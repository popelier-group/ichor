import numpy as np

from ichor.models.kernels.distance import Distance
from ichor.models.kernels.kernel import Kernel


class PeriodicKernel(Kernel):
    """Implemtation of the Periodic Kernel."""

    def __init__(self, thetas: np.ndarray, period_length: np.ndarray):
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

        self._thetas = thetas
        self._period_length = period_length

    @property
    def params(self):
        return self._thetas, self._period_length

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

        # implementation from gpytorch https://github.com/cornellius-gp/gpytorch/blob/master/gpytorch/kernels/periodic_kernel.py
        true_lengthscales = np.sqrt(1/self._thetas)

        x1_ = np.pi * (x1 / self._period_length)
        x2_ = np.pi * (x2 / self._period_length)
        x1_ = np.expand_dims(x1_, -2)
        x2_ = np.expand_dims(x2_, -3)
        diff = x1_ - x2_
        res = np.exp(np.multiply(np.divide(np.sum(np.power(np.sin(diff), 2), axis=-1), true_lengthscales), -2.0))
        return res

    def r(self, x_test: np.ndarray, x_train: np.ndarray) -> np.ndarray:
        """helper method to return x_test, x_train Periodic covariance matrix K(X*, X)"""
        return self.k(x_test, x_train)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """helper method to return symmetric square matrix x_train, x_train Periodic covariance matrix K(X, X)"""
        return self.k(x_train, x_train)

    def __repr__(self):
        return f"'{self.__class__.__name__}', thetas: {self._thetas}, period_length: {self._period_length}"