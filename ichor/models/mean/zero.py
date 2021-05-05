from ichor.models.mean.mean import Mean
import numpy as np


class ZeroMean(Mean):
    def value(self, x: np.ndarray) -> float:
        return 0.0

    def values(self, x: np.ndarray) -> np.ndarray:
        return np.zeros((x.shape[0]))
