from abc import ABC, abstractmethod

import numpy as np

from typing import Optional


class Kernel(ABC):
    """Base class for all kernels that implements dunder methods for addition or multiplication of separate kernels"""

    # TODO: figure out a good way to say if training data is standardized, normalized, etc. because kernels can be affected (for example cyclic RBF is affected)

    def __init__(self, active_dims: Optional[np.ndarray] = None):
        self._active_dims = active_dims

    @property
    def active_dims(self):
        if self._active_dims is not None:
            return self._active_dims
        return np.arange(len(self.params))

    @abstractmethod
    def params(self):
        pass

    @abstractmethod
    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """Calcualtes covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                A covariance matrix of shape (n, m)
        """

    def r(self, x_train: np.ndarray, x_test: np.ndarray) -> np.ndarray:
        """helper method to return x_test, x_train covariance matrix K(X*, X)"""
        return self.k(x_train, x_test)

    def R(self, x_train: np.ndarray) -> np.ndarray:
        """helper method to return symmetric square matrix x_train, x_train covariance matrix K(X, X)"""
        return self.k(x_train, x_train)

    @abstractmethod
    def __repr__(self):
        pass

    def __add__(self, other):
        return KernelSum(self, other)

    def __mul__(self, other):
        return KernelProd(self, other)


class KernelSum(Kernel):
    """Kernel addition implementation"""

    def __init__(self, k1: Kernel, k2: Kernel):
        self.k1 = k1
        self.k2 = k2

    @property
    def params(self):
        return np.concatenate(self.k1.params, self.k2.params)

    def k(self, xi, xj):
        return self.k1.k(xi, xj) + self.k2.k(xi, xj)

    def r(self, xi, x):
        return self.k1.r(xi, x) + self.k2.r(xi, x)

    def R(self, x):
        return self.k1.R(x) + self.k2.R(x)

    def __repr__(self):
        return f"({self.k1} + {self.k2})"


class KernelProd(Kernel):
    """Kernel multiplication implementation"""

    def __init__(self, k1, k2):
        self.k1 = k1
        self.k2 = k2

    @property
    def params(self):
        return np.concatenate(self.k1.params, self.k2.params)

    def k(self, xi, xj):
        return self.k1.k(xi, xj) * self.k2.k(xi, xj)

    def r(self, xi, x):
        return self.k1.r(xi, x) * self.k2.r(xi, x)

    def R(self, x):
        return self.k1.R(x) * self.k2.R(x)

    def __repr__(self):
        return f"({self.k1} * {self.k2})"
