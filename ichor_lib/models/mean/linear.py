from typing import IO

import numpy as np

from ichor_lib.models.mean.mean import Mean


class LinearMean(Mean):
    """A constant value that is used for the mean function. When no training data is present close to test points, covariance is low, therefore
    the predictions for the test points will be this constant mean value.

    :param value: A float to be used as the constant mean value
    """

    def __init__(self, beta: np.ndarray, xmin: np.ndarray, ymin: float):
        self._beta = beta
        self._xmin = xmin
        self._ymin = ymin

    def value(self, x: np.ndarray) -> np.ndarray:
        """Returns the constant mean value."""
        return np.matmul(x - self._xmin, self._beta) + self._ymin

    def write(self, f: IO):
        f.write("[mean]\n")
        f.write("type linear\n")
        f.write(f"beta {' '.join(map(str, self._beta))}\n")
        f.write(f"x_min {' '.join(map(str, self._xmin))}\n")
        f.write(f"y_min {self._ymin}\n")
