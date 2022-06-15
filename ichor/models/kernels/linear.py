from typing import IO, Optional

import numpy as np

from ichor.models.kernels.distance import Distance
from ichor.models.kernels.kernel import Kernel


class LinearKernel(Kernel):
    """Implementation of Radial Basis Function (RBF) kernel
    When each dimension has a separate lengthscale, this is also called the RBF-ARD kernel. Note that
    we use thetas instead of true lengthscales.

    .. math::
        \theta = \frac{1}{2l^2}

    where `l` is the lengthscale value.
    """

    def __init__(
        self,
        name: str,
        c: np.ndarray,
        active_dims: Optional[np.ndarray] = None,
    ):
        super().__init__(name, active_dims)
        self._c = c
        self._thetas = self._c

    @property
    def params(self):
        return self._c

    def k(self, x1: np.ndarray, x2: np.ndarray) -> np.ndarray:
        """
        Calculates RBF covariance matrix from two sets of points

        Args:
            :param: `x1` np.ndarray of shape n x ndimensions:
                First matrix of n points
            :param: `x2` np.ndarray of shape m x ndimensions:
                Second matrix of m points, can be identical to the first matrix `x1`

        Returns:
            :type: `np.ndarray`
                The RBF covariance matrix of shape (n, m)
        """

        result = np.empty((x1.shape[0], x2.shape[0]))
        for i, xi in enumerate(x1):
            for j, xj in enumerate(x2):
                result[i,j] = np.sum(self._c*xi*xj)
                
        return result

    def write(self, f: IO):
        f.write(f"[kernel.{self.name}]\n")
        f.write("type linear\n")
        f.write(f"number_of_dimensions {len(self.active_dims)}\n")
        f.write(
            f"active_dimensions {' '.join(map(str, self.active_dims+1))}\n"
        )
        f.write(f"c {' '.join(map(str, self._c))}\n")

    def __repr__(self):
        return f"{self.__class__.__name__}: c: {self._c}"
