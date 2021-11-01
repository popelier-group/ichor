import numpy as np
from typing import Optional

from ichor.models.kernels.distance import Distance
from ichor.models.kernels.kernel import Kernel


class PeriodicKernel(Kernel):
    """Implemtation of the Periodic Kernel."""

    def __init__(self, thetas: np.ndarray, period_length: np.ndarray, active_dims: Optional[np.ndarray] = None):
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
        super().__init__(active_dims)
        self._thetas = thetas
        self._period_length = period_length

    @property
    def params(self):
        return self._thetas, self._period_length

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calculates Periodic covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second matrix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The periodic covariance matrix of shape (n, m)
        """

        # implementation from gpytorch https://github.com/cornellius-gp/gpytorch/blob/master/gpytorch/kernels/periodic_kernel.py
        true_lengthscales = np.sqrt(1.0/(2 * self._thetas))
        true_lengthscales = true_lengthscales.reshape(-1,1,1)

        # get only dimensions which need periodic kernel
        x1_ = x1[:,self.active_dims]
        x2_ = x2[:,self.active_dims]

        # divide by period length and multiply by pi beforehand
        x1_ = np.pi * (x1_ / self._period_length)
        x2_ = np.pi * (x2_ / self._period_length)

        # expand dimensions to get a difference that is a 3d array.
        # The shape is n_dims x n_points_x1, n_points_x2
        x1_ = np.expand_dims(x1_.T, -1)
        x2_ = np.expand_dims(x2_.T, -2)
        diff = x1_ - x2_

        res = np.sin(diff)
        res = res / true_lengthscales
        res = res**2
        res = np.sum(res, axis=-3)
        res = -2.0 * res
        res = np.exp(res)
        return res

    def r(self, x_test: np.ndarray, x_train: np.ndarray) -> np.ndarray:
        """helper method to return x_test, x_train Periodic covariance matrix K(X*, X)"""
        return self.k(x_test, x_train)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """helper method to return symmetric square matrix x_train, x_train Periodic covariance matrix K(X, X)"""
        return self.k(x_train, x_train)

    def __repr__(self):
        return f"'{self.__class__.__name__}', thetas: {self._thetas}, period_length: {self._period_length}"