from typing import IO

import numpy as np
from ichor.core.models.mean.mean import Mean


class ConstantMean(Mean):
    """A constant value that is used for the mean function.
    When no training data is present close to test points, covariance is low, therefore
    the predictions for the test points will be this constant mean value.

    :param value: A float to be used as the constant mean value
    """

    def __init__(self, value: float):
        self._value = value

    def value(self, x: np.ndarray) -> np.ndarray:
        """Returns the constant mean value."""
        return np.full((x.shape[0]), self._value)

    def write(self, f: IO):
        f.write("[mean]\n")
        f.write("type constant\n")
        f.write(f"value {self._value}\n")
