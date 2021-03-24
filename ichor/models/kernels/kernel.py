from abc import ABC, abstractmethod
from collections.abc import Callable

import numpy as np


class Distance:
    def __init__(self, postprocess: Callable[np.array]):

        self._postprocess = postprocess

    def euclidean_squared_distance(
        self, x1: np.array, x2: np.array, postprocess: Callable[np.array]
    ) -> np.array:
        """ Calculates squared distance matrix between data points, uses array broadcasting and distance trick

        .. note::
            See the following websites for how array broadcasting and the distance trick work:
            https://medium.com/@souravdey/l2-distance-matrix-vectorization-trick-26aa3247ac6c
            https://stackoverflow.com/a/37903795

        .. note::
            Does not support batches (when x1 or x2 are 3D arrays)

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.array`
                The squared distance matrix of shape (`x1.shape[0]`, `x2.shape[0]`)
        """

        result = (
            -2 * np.dot(x1, x2.T)
            + np.sum(x2 ** 2, axis=1)
            + np.sum(x1 ** 2, axis=1)[:, np.newaxis]
        )
        result = result.clip(
            0
        )  # small negative values may occur when using quadratic expansion, so clip to 0 if that happens

        return self._postprocess(result) if postprocess else result

    def euclidean_distance(
        self, x1: np.array, x2: np.array, postprocess: Callable[np.array]
    ) -> np.array:
        """ Calculates distance matrix between data points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second marix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.array`
                The distance matrix of shape (`x1.shape[0]`, `x2.shape[0]`)
         """

        result = self.euclidean_squared_distance(x1, x2)
        result = np.srqt(result)

        return self._postprocess(result) if postprocess else result


class Kernel(ABC):
    """ Base class for all kernels that implements dunder methods for addition or multiplication of separate kernels"""

    @property
    def params(self):
        # TODO: Convert this to error
        print("Error: Params not defined for specified kernel")
        quit()

    @abstractmethod
    def k(self):
        """"""
        pass

    @abstractmethod
    def r(self):
        pass

    @abstractmethod
    def R(self):
        pass

    def __add__(self, other):
        return KernelSum(self, other)

    def __mul__(self, other):
        return KernelProd(self, other)


class KernelSum(Kernel):
    """ Kernel addition implementation"""

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


class KernelProd(Kernel):
    """ Kernel multiplication implementation"""

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
