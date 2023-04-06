from typing import IO

import numpy as np
from ichor.core.models.mean.mean import Mean


class QuadraticMean(Mean):
    """A quadratic mean"""

    def __init__(self, beta: np.ndarray, xmin: np.ndarray, ymin: float):
        self._beta = beta[:, np.newaxis]
        self._xmin = xmin
        self._ymin = ymin

    def value(self, x: np.ndarray) -> np.ndarray:
        """Returns the constant mean value."""
        a = x - self._xmin
        return (np.matmul(a * a, self._beta) + self._ymin).flatten()

    def write(self, f: IO):
        f.write("[mean]\n")
        f.write("type quadratic\n")
        f.write(f"beta {' '.join(map(str, self._beta))}\n")
        f.write(f"x_min {' '.join(map(str, self._xmin))}\n")
        f.write(f"y_min {self._ymin}\n")
