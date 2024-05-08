import numpy as np
from ichor.core.models.mean.mean import Mean


class LinearMean(Mean):
    """A linear mean."""

    def __init__(self, beta: np.ndarray, xmin: np.ndarray, ymin: float):
        self._beta = beta
        self._xmin = xmin
        self._ymin = ymin

    def value(self, x: np.ndarray) -> np.ndarray:
        """Returns the constant mean value."""
        return np.matmul(x - self._xmin, self._beta) + self._ymin

    def write_str(self) -> str:

        write_str = ""

        write_str += "[mean]\n"
        write_str += "type linear\n"
        write_str += f"beta {' '.join(map(str, self._beta))}\n"
        write_str += f"x_min {' '.join(map(str, self._xmin))}\n"
        write_str += f"y_min {self._ymin}\n"

        return write_str
